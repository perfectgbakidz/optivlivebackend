# app/services/webhook_service.py
from fastapi import HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from uuid import uuid4
import stripe
import json
import logging

from app.utils.common import generate_referral_code
from app.config import settings
from app.services.transaction_service import distribute_signup_bonus

logger = logging.getLogger(__name__)
stripe.api_key = settings.STRIPE_SECRET_KEY


async def handle_stripe_webhook(request: Request, db: AsyncSession):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    # -----------------------------
    # Event parsing
    # -----------------------------
    if settings.DEBUG:
        # Bypass Stripe signature for local testing
        try:
            event = json.loads(payload.decode("utf-8"))
            logger.warning("⚠️ DEBUG mode: skipping Stripe signature verification")
        except Exception as e:
            logger.error(f"❌ Failed to parse test payload: {e}")
            raise HTTPException(status_code=400, detail="Invalid test payload")
    else:
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
        except stripe.error.SignatureVerificationError as e:  # type: ignore
            logger.error(f"❌ Invalid Stripe signature: {e}")
            raise HTTPException(status_code=400, detail="Invalid Stripe signature")
        except Exception as e:
            logger.error(f"❌ Failed to parse Stripe event: {e}")
            raise HTTPException(status_code=400, detail="Invalid payload")

    logger.debug(f"📦 Stripe event received: {json.dumps(event)}")

    # -----------------------------
    # Only handle payment success
    # -----------------------------
    if event["type"] != "payment_intent.succeeded":
        logger.info(f"ℹ️ Ignoring event type {event['type']}")
        return {"received": True}

    intent = event["data"]["object"]
    pending_id = intent["metadata"].get("pending_registration_id")

    if not pending_id:
        logger.warning("⚠️ payment_intent missing pending_registration_id in metadata")
        return {"received": True}

    logger.info(f"✅ Stripe webhook triggered for pending_id={pending_id}")

    # -----------------------------
    # Lookup pending registration
    # -----------------------------
    query = text("SELECT * FROM pending_registrations WHERE id = :id LIMIT 1")
    result = await db.execute(query, {"id": pending_id})
    pending = result.fetchone()
    logger.info(f"📌 Pending registration row: {pending}")

    if not pending:
        logger.warning("⚠️ Pending registration not found or already processed.")
        return {"received": True}

    # -----------------------------
    # Create final user
    # -----------------------------
    try:
        user_id = str(uuid4())
        referral_code = generate_referral_code()

        insert_user = text("""
            INSERT INTO users (
                id, email, username, password_hash, first_name, last_name,
                referral_code, referred_by_code,
                role, status, withdrawal_status, balance,
                is_kyc_verified, is_2fa_enabled, has_pin
            )
            VALUES (
                :id, :email, :username, :password_hash, :first_name, :last_name,
                :referral_code, :referred_by_code,
                'user', 'active', 'active', 0.00,
                false, false, false
            )
        """)

        params = {
            "id": user_id,
            "email": pending._mapping["email"],
            "username": pending._mapping["username"],
            "password_hash": pending._mapping["password_hash"],
            "first_name": pending._mapping["first_name"],
            "last_name": pending._mapping["last_name"],
            "referral_code": referral_code,                     # 🎯 new code
            "referred_by_code": pending._mapping["referrer_code"],  # 🎯 inviter’s code
        }

        await db.execute(insert_user, params)
        logger.info(f"📝 Inserted user with params: {params}")

        # Distribute referral bonus
        signup_fee = 50
        await distribute_signup_bonus(
            new_user_id=user_id,
            referrer_code=pending._mapping["referrer_code"],
            signup_fee=signup_fee,
            db=db
        )

        # Delete pending registration
        delete_pending = text("DELETE FROM pending_registrations WHERE id = :id")
        await db.execute(delete_pending, {"id": pending_id})

        await db.commit()
        logger.info(f"🎉 User {user_id} created and pending_id={pending_id} removed")

    except Exception as e:
        logger.exception(f"❌ Failed to move pending {pending_id} to users: {e}")
        await db.rollback()

    return {"received": True}

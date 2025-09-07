# app/services/webhook_service.py
from fastapi import HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from uuid import uuid4
import stripe

from app.utils.common import generate_referral_code
from app.config import settings
from app.services.transaction_service import distribute_signup_bonus  # ✅ NEW

stripe.api_key = settings.STRIPE_SECRET_KEY


async def handle_stripe_webhook(request: Request, db: AsyncSession):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except stripe.error.SignatureVerificationError:  # type: ignore
        raise HTTPException(status_code=400, detail="Invalid Stripe signature")

    if event["type"] != "payment_intent.succeeded":
        return {"received": True}

    intent = event["data"]["object"]
    pending_id = intent["metadata"].get("pending_registration_id")

    # Lookup pending registration
    query = text("SELECT * FROM pending_registrations WHERE id = :id LIMIT 1")
    result = await db.execute(query, {"id": pending_id})
    pending = result.fetchone()
    if not pending:
        return {"received": True}  # expired or already processed

    # Create final user
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
            'user', 'active', 'active', '0.00',
            false, false, false
        )
    """)
    await db.execute(insert_user, {
        "id": user_id,
        "email": pending.email,
        "username": pending.username,
        "password_hash": pending.hashed_password,
        "first_name": pending.first_name,
        "last_name": pending.last_name,
        "referral_code": referral_code,
        "referred_by_code": pending.referrer_code,
    })

    # 🚀 Distribute referral bonuses (signup fee = £50)
    signup_fee = 50
    await distribute_signup_bonus(
        new_user_id=user_id,
        referrer_code=pending.referrer_code,
        signup_fee=signup_fee,
        db=db
    )

    # Delete from pending_registrations
    delete_pending = text("DELETE FROM pending_registrations WHERE id = :id")
    await db.execute(delete_pending, {"id": pending_id})

    await db.commit()

    return {"received": True}

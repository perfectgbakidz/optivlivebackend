from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from datetime import datetime
from uuid import uuid4
from typing import List, Optional

from app.schemas.transaction_schemas import TransactionResponse
from app.utils.stripe_client import create_payment_intent
from app.utils.common import generate_transaction_ref
from app.config import settings  # ✅ pull MASTER_REFERRAL_CODE from config


# -----------------------------
# LIST USER TRANSACTIONS
# -----------------------------
async def list_transactions(user, page: int, page_size: int, db: AsyncSession) -> List[TransactionResponse]:
    offset = (page - 1) * page_size
    query = text("""
        SELECT * FROM transactions
        WHERE user_id = :uid
        ORDER BY created_at DESC
        LIMIT :limit OFFSET :offset
    """)
    result = await db.execute(query, {"uid": user["id"], "limit": page_size, "offset": offset})
    records = result.fetchall()

    return [
        TransactionResponse(
            id=str(r.id),
            type=r.type,
            amount=str(r.amount),
            currency=r.currency,
            status=r.status,
            reference=r.reference,
            created_at=r.created_at,
            user_id=getattr(r, "user_id", None),
            referee_id=getattr(r, "referee_id", None),
            tier=getattr(r, "tier", None),
            note=getattr(r, "note", None),
        )
        for r in records
    ]


# -----------------------------
# GET SINGLE TRANSACTION
# -----------------------------
async def get_transaction(user, transaction_id: str, db: AsyncSession) -> TransactionResponse:
    query = text("SELECT * FROM transactions WHERE id = :id AND user_id = :uid")
    result = await db.execute(query, {"id": transaction_id, "uid": user["id"]})
    record = result.fetchone()
    if not record:
        raise HTTPException(status_code=404, detail="Transaction not found")

    return TransactionResponse(
        id=str(record.id),
        type=record.type,
        amount=str(record.amount),
        currency=record.currency,
        status=record.status,
        reference=record.reference,
        created_at=record.created_at,
        user_id=getattr(record, "user_id", None),
        referee_id=getattr(record, "referee_id", None),
        tier=getattr(record, "tier", None),
        note=getattr(record, "note", None),
    )


# -----------------------------
# CREATE DEPOSIT (Stripe PaymentIntent)
# -----------------------------
async def create_deposit(user, amount: str, currency: str = "usd", db: AsyncSession = None):
    try:
        intent = create_payment_intent(
            amount=int(float(amount) * 100),
            currency=currency,
            metadata={"user_id": user["id"], "type": "deposit"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stripe error: {str(e)}")

    tid = str(uuid4())
    ref = generate_transaction_ref("DEP")
    insert_q = text("""
        INSERT INTO transactions (id, user_id, type, amount, currency, status, reference, created_at)
        VALUES (:id, :uid, 'deposit', :amt, :cur, 'pending', :ref, :dt)
    """)
    await db.execute(insert_q, {
        "id": tid,
        "uid": user["id"],
        "amt": amount,
        "cur": currency,
        "ref": ref,
        "dt": datetime.utcnow(),
    })
    await db.commit()

    return {"client_secret": intent.client_secret, "transaction_id": tid, "reference": ref}


# -----------------------------
# LOG WITHDRAWAL (after approval)
# -----------------------------
async def log_withdrawal(user_id: str, amount: str, currency: str = "usd", db: AsyncSession = None):
    tid = str(uuid4())
    ref = generate_transaction_ref("WDR")
    insert_q = text("""
        INSERT INTO transactions (id, user_id, type, amount, currency, status, reference, created_at)
        VALUES (:id, :uid, 'withdrawal', :amt, :cur, 'completed', :ref, :dt)
    """)
    await db.execute(insert_q, {
        "id": tid,
        "uid": user_id,
        "amt": amount,
        "cur": currency,
        "ref": ref,
        "dt": datetime.utcnow(),
    })
    await db.commit()
    return tid


# -----------------------------
# LOG REFERRAL BONUS
# -----------------------------
async def log_referral_bonus(user_id: str, referee_id: str, amount: str, tier: int, db: AsyncSession = None):
    tid = str(uuid4())
    ref = generate_transaction_ref("REF")
    insert_q = text("""
        INSERT INTO transactions (id, user_id, type, amount, currency, status, reference, created_at, referee_id, tier)
        VALUES (:id, :uid, 'referral_bonus', :amt, 'usd', 'completed', :ref, :dt, :referee, :tier)
    """)
    await db.execute(insert_q, {
        "id": tid,
        "uid": user_id,
        "amt": amount,
        "ref": ref,
        "dt": datetime.utcnow(),
        "referee": referee_id,
        "tier": tier,
    })
    return tid


# -----------------------------
# LOG ADMIN CREDIT (MASTERKEY leftover)
# -----------------------------
async def log_admin_credit(user_id: str, amount: str, note: str, db: AsyncSession = None):
    tid = str(uuid4())
    ref = generate_transaction_ref("ADM")
    insert_q = text("""
        INSERT INTO transactions (id, user_id, type, amount, currency, status, reference, created_at, note)
        VALUES (:id, :uid, 'admin_credit', :amt, 'usd', 'completed', :ref, :dt, :note)
    """)
    await db.execute(insert_q, {
        "id": tid,
        "uid": user_id,
        "amt": amount,
        "ref": ref,
        "dt": datetime.utcnow(),
        "note": note,
    })
    return tid



# -----------------------------
# DISTRIBUTE SIGNUP BONUS (6 tiers + MASTERKEY fallback)
# -----------------------------
async def distribute_signup_bonus(new_user_id: str, referrer_code: Optional[str], signup_fee: float, db: AsyncSession):
    if not referrer_code:
        return

    master_key = settings.MASTER_REFERRAL_CODE  # ✅ use config
    percentages = [0.10, 0.085, 0.07225, 0.0614, 0.0522, 0.044]  # Fixed percentages per tier

    total_distributed = 0.0
    current_code = referrer_code

    for tier, pct in enumerate(percentages, start=1):
        query = text("SELECT id, referred_by_code FROM users WHERE referral_code = :code LIMIT 1")
        result = await db.execute(query, {"code": current_code})
        referrer = result.fetchone()
        if not referrer:
            break

        bonus_amount = round(signup_fee * pct, 2)
        total_distributed += bonus_amount

        # Update referrer balance
        update_balance = text("UPDATE users SET balance = balance + :amt WHERE id = :uid")
        await db.execute(update_balance, {"amt": bonus_amount, "uid": referrer.id})

        # Log referral bonus transaction
        await log_referral_bonus(referrer.id, new_user_id, str(bonus_amount), tier, db)

        # Move to next level up
        current_code = referrer.referred_by_code

    # Any leftover goes to MASTERKEY
    leftover = round(signup_fee - total_distributed, 2)
    if leftover > 0:
        result = await db.execute(
            text("SELECT id FROM users WHERE referral_code = :code LIMIT 1"),
            {"code": master_key}
        )
        master = result.fetchone()
        if master:
            update_balance = text("UPDATE users SET balance = balance + :amt WHERE id = :uid")
            await db.execute(update_balance, {"amt": leftover, "uid": master.id})
            await log_admin_credit(master.id, str(leftover), f"Leftover from signup of {new_user_id}", db)

    await db.commit()

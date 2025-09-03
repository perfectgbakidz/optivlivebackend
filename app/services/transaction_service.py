from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from datetime import datetime
from uuid import uuid4
from typing import List

from app.schemas.transaction_schemas import TransactionResponse
from app.utils.stripe_handler import create_payment_intent
from app.utils.common import generate_transaction_ref


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
    )


# -----------------------------
# CREATE DEPOSIT (Stripe PaymentIntent)
# -----------------------------
async def create_deposit(user, amount: str, currency: str = "usd", db: AsyncSession = None):
    # Create Stripe PaymentIntent
    try:
        intent = create_payment_intent(
            amount=int(float(amount) * 100),  # Stripe expects cents
            currency=currency,
            metadata={"user_id": user["id"], "type": "deposit"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stripe error: {str(e)}")

    # Insert transaction record
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
async def log_referral_bonus(user_id: str, referee_id: str, amount: str, db: AsyncSession = None):
    tid = str(uuid4())
    ref = generate_transaction_ref("REF")
    insert_q = text("""
        INSERT INTO transactions (id, user_id, type, amount, currency, status, reference, created_at)
        VALUES (:id, :uid, 'referral_bonus', :amt, 'usd', 'completed', :ref, :dt)
    """)
    await db.execute(insert_q, {
        "id": tid,
        "uid": user_id,
        "amt": amount,
        "ref": ref,
        "dt": datetime.utcnow(),
    })
    await db.commit()
    return tid

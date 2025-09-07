from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from datetime import datetime
from uuid import uuid4
from typing import List

from app.database import get_db
from app.schemas.withdrawal_schemas import WithdrawalCreateRequest, WithdrawalResponse
from app.utils.stripe_client import create_payout


# -----------------------------
# LIST USER WITHDRAWALS
# -----------------------------
async def list_withdrawals(user, db: AsyncSession = Depends(get_db)) -> List[WithdrawalResponse]:
    query = text("SELECT * FROM withdrawals WHERE user_id = :uid ORDER BY requested_at DESC")
    result = await db.execute(query, {"uid": user["id"]})
    records = result.fetchall()

    return [
        WithdrawalResponse(
            id=str(r.id),
            amount=str(r.amount),
            destination_address=r.destination_address,
            status=r.status,
            requested_at=r.requested_at,
            processed_at=r.processed_at,
        )
        for r in records
    ]


# -----------------------------
# CREATE WITHDRAWAL REQUEST
# -----------------------------
async def create_withdrawal(user, payload: WithdrawalCreateRequest, db: AsyncSession = Depends(get_db)) -> WithdrawalResponse:
    # 1. Check balance
    balance_q = text("SELECT balance, is_kyc_verified, has_pin FROM users WHERE id = :id")
    result = await db.execute(balance_q, {"id": user["id"]})
    record = result.fetchone()

    if not record:
        raise HTTPException(status_code=404, detail="User not found")

    if not record.is_kyc_verified:
        raise HTTPException(status_code=403, detail="KYC required before withdrawals")

    if not record.has_pin:
        raise HTTPException(status_code=403, detail="Withdrawal PIN must be set")

    if float(record.balance) < float(payload.amount):
        raise HTTPException(status_code=400, detail="Insufficient balance")

    # 2. Deduct balance immediately
    new_balance = float(record.balance) - float(payload.amount)
    update_balance_q = text("UPDATE users SET balance = :bal WHERE id = :id")
    await db.execute(update_balance_q, {"id": user["id"], "bal": str(new_balance)})

    # 3. Insert withdrawal request
    wid = str(uuid4())
    insert_q = text("""
        INSERT INTO withdrawals (id, user_id, amount, destination_address, status, requested_at)
        VALUES (:id, :uid, :amt, :dest, 'pending', :req)
    """)
    await db.execute(insert_q, {
        "id": wid,
        "uid": user["id"],
        "amt": payload.amount,
        "dest": payload.destination_address,
        "req": datetime.utcnow(),
    })
    await db.commit()

    return WithdrawalResponse(
        id=wid,
        amount=payload.amount,
        destination_address=payload.destination_address,
        status="pending",
        requested_at=datetime.utcnow(),
        processed_at=None,
    )


# -----------------------------
# ADMIN APPROVAL (used in admin_service)
# -----------------------------
async def approve_withdrawal(withdrawal_id: str, db: AsyncSession):
    # Fetch withdrawal
    query = text("SELECT * FROM withdrawals WHERE id = :id AND status = 'pending'")
    result = await db.execute(query, {"id": withdrawal_id})
    record = result.fetchone()
    if not record:
        raise HTTPException(status_code=404, detail="Withdrawal not found or already processed")

    # Trigger Stripe payout
    try:
        payout = create_payout(
            amount=int(float(record.amount) * 100),  # Stripe expects cents
            currency="usd",
            destination=record.destination_address,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stripe payout failed: {str(e)}")

    # Update withdrawal status
    update_q = text("UPDATE withdrawals SET status = 'approved', processed_at = :dt WHERE id = :id")
    await db.execute(update_q, {"id": withdrawal_id, "dt": datetime.utcnow()})
    await db.commit()

    return {"message": f"Withdrawal {withdrawal_id} approved", "stripe_payout_id": payout.id}


async def deny_withdrawal(withdrawal_id: str, db: AsyncSession):
    query = text("UPDATE withdrawals SET status = 'denied', processed_at = :dt WHERE id = :id AND status = 'pending'")
    await db.execute(query, {"id": withdrawal_id, "dt": datetime.utcnow()})
    await db.commit()
    return {"message": f"Withdrawal {withdrawal_id} denied"}

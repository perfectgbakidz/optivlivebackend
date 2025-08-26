from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from decimal import Decimal

from .. import models, schemas, database, auth
from ..utils import verify_password, hash_password

router = APIRouter(prefix="/withdrawals", tags=["Withdrawals"])

# Fees + Rules
MIN_WITHDRAWAL = Decimal("10.00")
FLAT_FEE = Decimal("1.50")
PERCENT_FEE = Decimal("0.03")


# --------------------------
# Create a withdrawal request
# --------------------------
@router.post("/", response_model=schemas.WithdrawalResponse)
def create_withdrawal(
    data: schemas.WithdrawalCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    # ✅ Enforce KYC approval
    if not current_user.is_kyc_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="KYC must be approved before withdrawals."
        )

    # ✅ Enforce PIN protection
    if not current_user.pin_hash:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must set a withdrawal PIN before making withdrawals."
        )

    # ✅ Validate balance + amount
    try:
        balance = Decimal(current_user.balance)
        amount = Decimal(data.amount)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid amount format."
        )

    if amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Withdrawal amount must be positive."
        )

    # ✅ Minimum withdrawal
    if amount < MIN_WITHDRAWAL:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Minimum withdrawal is {MIN_WITHDRAWAL} GBP."
        )

    if balance < amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Insufficient balance."
        )

    # ✅ Apply fees
    fee = FLAT_FEE + (amount * PERCENT_FEE)
    final_amount = amount - fee

    if final_amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Withdrawal too small after fees."
        )

    # ✅ Deduct requested amount immediately
    current_user.balance = str(balance - amount)

    # ✅ Create withdrawal request
    withdrawal = models.Withdrawal(
        user_id=current_user.id,
        amount=str(final_amount),   # ✅ amount user will actually receive
        fee=str(fee),               # ✅ store fee separately
        bank_name=data.bank_name,
        account_number=data.account_number,
        account_name=data.account_name,
        status="pending"
    )
    db.add(withdrawal)

    # ✅ Log transaction (keep original requested amount)
    tx = models.Transaction(
        user_id=current_user.id,
        type="withdrawal",
        amount=float(amount),  # original request
        status="pending"
    )
    db.add(tx)

    db.commit()
    db.refresh(withdrawal)

    return withdrawal


# --------------------------
# List user withdrawals
# --------------------------
@router.get("/", response_model=List[schemas.WithdrawalResponse])
def list_withdrawals(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    withdrawals = (
        db.query(models.Withdrawal)
        .filter(models.Withdrawal.user_id == current_user.id)
        .order_by(models.Withdrawal.id.desc())
        .all()
    )
    return withdrawals

# app/routers/users.py
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.user_schemas import (
    ChangePasswordRequest, SetPinRequest, ChangePinRequest, VerifyPinRequest,
    UserUpdateRequest, UserProfileResponse,
    WithdrawalRequest, WithdrawalResponse
)
from app.schemas.transaction_schemas import TransactionResponse
from app.services import user_service, transaction_service
from app.dependencies import get_current_user
from app.database import get_db

router = APIRouter(prefix="/users", tags=["Users"])


# -----------------------------
# PROFILE
# -----------------------------
@router.get("/profile/", response_model=UserProfileResponse)
async def get_profile(
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await user_service.get_profile(user, db)


@router.patch("/profile/", response_model=UserProfileResponse)
async def update_profile(
    payload: UserUpdateRequest,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await user_service.update_profile(user, payload, db)


# -----------------------------
# PASSWORD
# -----------------------------
@router.post("/change-password/")
async def change_password(
    payload: ChangePasswordRequest,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await user_service.change_password(user, payload, db)


# -----------------------------
# PIN
# -----------------------------
@router.post("/set-pin/")
async def set_pin(
    payload: SetPinRequest,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await user_service.set_pin(user, payload, db)


@router.patch("/change-pin/")
async def change_pin(
    payload: ChangePinRequest,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await user_service.change_pin(user, payload, db)


@router.post("/verify-pin/")
async def verify_pin(
    payload: VerifyPinRequest,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await user_service.verify_user_pin(user, payload, db)


# -----------------------------
# WITHDRAWALS
# -----------------------------
@router.post("/withdrawals/", response_model=WithdrawalResponse)
async def request_withdrawal(
    payload: WithdrawalRequest,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await user_service.request_withdrawal(user, payload, db)


@router.get("/withdrawals/", response_model=list[WithdrawalResponse])
async def list_withdrawals(
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await user_service.list_withdrawals(user, db)


# -----------------------------
# TRANSACTIONS
# -----------------------------
@router.get("/transactions/", response_model=list[TransactionResponse])
async def list_transactions(
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    return await transaction_service.list_transactions(user, limit, offset, db)

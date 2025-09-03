from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.user_schemas import (
    ChangePasswordRequest, SetPinRequest, ChangePinRequest, VerifyPinRequest,
    UserUpdateRequest, UserProfileResponse
)
from app.services import user_service
from app.dependencies import get_current_user
from app.database import get_db

router = APIRouter(prefix="/users", tags=["Users"])


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


@router.post("/change-password/")
async def change_password(
    payload: ChangePasswordRequest,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await user_service.change_password(user, payload, db)


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

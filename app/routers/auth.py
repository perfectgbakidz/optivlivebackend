from fastapi import APIRouter, Depends
from app.schemas.auth_schemas import (
    LoginRequest, RegisterRequest, TwoFAVerifyRequest,
    PasswordResetRequest, PasswordResetConfirmRequest,
    TokenResponse, TwoFARequiredResponse
)
from app.services import auth_service
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login/", response_model=TokenResponse | TwoFARequiredResponse)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    return await auth_service.login(payload, db)


@router.post("/register/", response_model=TokenResponse)
async def register(payload: RegisterRequest, db: AsyncSession = Depends(get_db)):
    return await auth_service.register(payload, db)


@router.post("/2fa/verify/", response_model=TokenResponse)
async def verify_2fa(payload: TwoFAVerifyRequest, db: AsyncSession = Depends(get_db)):
    return await auth_service.verify_2fa(payload, db)


@router.post("/password/reset/")
async def password_reset(payload: PasswordResetRequest, db: AsyncSession = Depends(get_db)):
    return await auth_service.password_reset(payload, db)


@router.post("/password/reset/confirm/")
async def password_reset_confirm(payload: PasswordResetConfirmRequest, db: AsyncSession = Depends(get_db)):
    return await auth_service.password_reset_confirm(payload, db)

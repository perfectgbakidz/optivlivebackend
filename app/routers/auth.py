from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.auth_schemas import (
    LoginRequest, RegisterRequest, TwoFAVerifyRequest,
    PasswordResetRequest, PasswordResetConfirmRequest,
    TokenResponse, TwoFARequiredResponse,
    InitiateRegistrationRequest, InitiateRegistrationResponse,
)
from app.services import auth_service, webhook_service
from app.database import get_db

router = APIRouter(prefix="/auth", tags=["Authentication"])


# -----------------------------
# LOGIN
# -----------------------------
@router.post("/login/", response_model=TokenResponse | TwoFARequiredResponse)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    return await auth_service.login(payload, db)


# -----------------------------
# REGISTRATION (NEW FLOW)
# -----------------------------
@router.post("/initiate-registration/", response_model=InitiateRegistrationResponse)
async def initiate_registration(payload: InitiateRegistrationRequest, db: AsyncSession = Depends(get_db)):
    """
    Step 1: Validate registration data, create payment intent, and store
    pending registration in DB. Returns Stripe client_secret.
    """
    return await auth_service.initiate_registration(payload, db)


@router.post("/webhooks/stripe/")
async def stripe_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Step 2: Stripe calls this after payment succeeds.
    Final user account is created here.
    """
    raw_body = await request.body()
    sig_header = request.headers.get("stripe-signature")

    if not sig_header:
        raise HTTPException(status_code=400, detail="Missing Stripe signature")

    # ✅ delegate to webhook_service, not auth_service
    return await webhook_service.handle_stripe_webhook(raw_body, sig_header, db)


# -----------------------------
# 2FA
# -----------------------------
@router.post("/2fa/verify/", response_model=TokenResponse)
async def verify_2fa(payload: TwoFAVerifyRequest, db: AsyncSession = Depends(get_db)):
    return await auth_service.verify_2fa(payload, db)


# -----------------------------
# PASSWORD RESET
# -----------------------------
@router.post("/password/reset/")
async def password_reset(payload: PasswordResetRequest, db: AsyncSession = Depends(get_db)):
    return await auth_service.password_reset(payload, db)


@router.post("/password/reset/confirm/")
async def password_reset_confirm(payload: PasswordResetConfirmRequest, db: AsyncSession = Depends(get_db)):
    return await auth_service.password_reset_confirm(payload, db)

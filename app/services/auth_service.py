from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from uuid import uuid4
from datetime import datetime, timedelta
import stripe

from app.schemas.auth_schemas import (
    LoginRequest,
    InitiateRegistrationRequest,
    InitiateRegistrationResponse,
    TwoFAVerifyRequest,
    PasswordResetRequest,
    PasswordResetConfirmRequest,
    TokenResponse,
    TwoFARequiredResponse,
)
from app.database import get_db
from app.utils.security import hash_password, verify_password
from app.utils.jwt_handler import create_access_token, create_refresh_token
from app.config import settings


# -----------------------------
# STRIPE INIT
# -----------------------------
stripe.api_key = settings.STRIPE_SECRET_KEY


# -----------------------------
# LOGIN
# -----------------------------
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    query = text("SELECT * FROM users WHERE email = :email LIMIT 1")
    result = await db.execute(query, {"email": payload.email})
    user = result.fetchone()

    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    # If 2FA is enabled, require second step
    if user.is_2fa_enabled:
        return TwoFARequiredResponse(two_factor_required=True, user_id=str(user.id))

    token_data = {
        "sub": str(user.id),
        "email": user.email,
        "username": user.username,
        "role": user.role,
    }
    access = create_access_token(
        token_data, timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    refresh = create_refresh_token(token_data)

    return TokenResponse(access=access, refresh=refresh)


# -----------------------------
# INITIATE REGISTRATION (Step 1)
# -----------------------------
async def initiate_registration(
    payload: InitiateRegistrationRequest, db: AsyncSession = Depends(get_db)
):
    # Check if email/username already exists in users
    query = text(
        "SELECT 1 FROM users WHERE email = :email OR username = :username LIMIT 1"
    )
    result = await db.execute(
        query, {"email": payload.email, "username": payload.username}
    )
    if result.fetchone():
        raise HTTPException(
            status_code=400, detail="Email or username already exists"
        )

    # Check if already pending
    pending_query = text(
        "SELECT 1 FROM pending_registrations WHERE email = :email LIMIT 1"
    )
    result = await db.execute(pending_query, {"email": payload.email})
    if result.fetchone():
        raise HTTPException(
            status_code=400,
            detail="A pending registration already exists for this email",
        )

    # Hash password & prepare pending registration
    hashed_pw = hash_password(payload.password)
    pending_id = str(uuid4())

    # Use Python for consistency (avoid DB timezone mismatch)
    created_at = datetime.utcnow()
    expires_at = created_at + timedelta(minutes=30)

    insert_pending = text(
        """
        INSERT INTO pending_registrations (
            id, email, username, password_hash, first_name, last_name, referred_by_code,
            status, created_at, expires_at
        )
        VALUES (
            :id, :email, :username, :password_hash, :first_name, :last_name,
            :referred_by_code, 'pending', :created_at, :expires_at
        )
    """
    )
    await db.execute(
        insert_pending,
        {
            "id": pending_id,
            "email": payload.email,
            "username": payload.username,
            "password_hash": hashed_pw,
            "first_name": payload.first_name,
            "last_name": payload.last_name,
            # 👇 FIXED: now uses schema field referred_by_code
            "referred_by_code": payload.referred_by_code,
            "created_at": created_at,
            "expires_at": expires_at,
        },
    )
    await db.commit()

    # Create Stripe PaymentIntent
    payment_intent = stripe.PaymentIntent.create(
        amount=5000,  # £50.00 in pence
        currency="gbp",
        metadata={"pending_registration_id": pending_id},
    )

    # Update pending registration with PaymentIntent ID
    update_query = text(
        """
        UPDATE pending_registrations
        SET stripe_payment_intent_id = :pi_id, updated_at = :updated_at
        WHERE id = :id
    """
    )
    await db.execute(
        update_query,
        {"pi_id": payment_intent.id, "updated_at": datetime.utcnow(), "id": pending_id},
    )
    await db.commit()

    return InitiateRegistrationResponse(client_secret=payment_intent.client_secret)


# -----------------------------
# 2FA VERIFY (placeholder)
# -----------------------------
async def verify_2fa(payload: TwoFAVerifyRequest, db: AsyncSession = Depends(get_db)):
    # TODO: validate token using pyotp and user.two_fa_secret
    token_data = {
        "sub": payload.user_id,
        "email": "dummy@example.com",
        "username": "dummy",
        "role": "user",
    }
    access = create_access_token(
        token_data, timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    refresh = create_refresh_token(token_data)
    return TokenResponse(access=access, refresh=refresh)


# -----------------------------
# PASSWORD RESET
# -----------------------------
async def password_reset(
    payload: PasswordResetRequest, db: AsyncSession = Depends(get_db)
):
    # TODO: generate reset token, email link to user
    return {"message": "Password reset link sent"}


async def password_reset_confirm(
    payload: PasswordResetConfirmRequest, db: AsyncSession = Depends(get_db)
):
    # TODO: verify reset token, update hashed password in DB
    return {"message": "Password reset successful"}

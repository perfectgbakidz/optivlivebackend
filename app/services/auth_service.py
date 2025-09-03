from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from uuid import uuid4
from datetime import timedelta

from app.schemas.auth_schemas import (
    LoginRequest, RegisterRequest, TwoFAVerifyRequest,
    PasswordResetRequest, PasswordResetConfirmRequest,
    TokenResponse, TwoFARequiredResponse
)
from app.database import get_db
from app.utils.security import hash_password, verify_password
from app.utils.jwt_handler import create_access_token, create_refresh_token
from app.utils.common import generate_referral_code
from app.config import settings


# -----------------------------
# LOGIN
# -----------------------------
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    query = text("SELECT * FROM users WHERE email = :email LIMIT 1")
    result = await db.execute(query, {"email": payload.email})
    user = result.fetchone()

    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    # If 2FA is enabled, require second step
    if user.is_2fa_enabled:
        return TwoFARequiredResponse(two_factor_required=True, user_id=str(user.id))

    # Otherwise, issue tokens
    token_data = {
        "sub": str(user.id),
        "email": user.email,
        "username": user.username,
        "role": user.role,
    }
    access = create_access_token(token_data, timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    refresh = create_refresh_token(token_data)

    return TokenResponse(
        access=access,
        refresh=refresh
    )


# -----------------------------
# REGISTER
# -----------------------------
async def register(payload: RegisterRequest, db: AsyncSession = Depends(get_db)):
    # Check if email/username already exists
    query = text("SELECT 1 FROM users WHERE email = :email OR username = :username LIMIT 1")
    result = await db.execute(query, {"email": payload.email, "username": payload.username})
    existing = result.fetchone()
    if existing:
        raise HTTPException(status_code=400, detail="Email or username already exists")

    hashed_pw = hash_password(payload.password)
    referral_code = generate_referral_code()

    user_id = str(uuid4())

    insert_query = text("""
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

    await db.execute(insert_query, {
        "id": user_id,
        "email": payload.email,
        "username": payload.username,
        "password_hash": hashed_pw,
        "first_name": payload.first_name,
        "last_name": payload.last_name,
        "referral_code": referral_code,
        "referred_by_code": payload.referral_code if payload.referral_code else None,
    })
    await db.commit()

    # 🚀 TODO: If payload.referral_code is valid, apply referral bonus logic here.

    token_data = {
        "sub": user_id,
        "email": payload.email,
        "username": payload.username,
        "role": "user",
    }
    access = create_access_token(token_data, timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    refresh = create_refresh_token(token_data)

    return TokenResponse(
        access=access,
        refresh=refresh
    )


# -----------------------------
# 2FA VERIFY (placeholder)
# -----------------------------
async def verify_2fa(payload: TwoFAVerifyRequest, db: AsyncSession = Depends(get_db)):
    # TODO: validate token using pyotp and user.two_fa_secret
    token_data = {
        "sub": payload.user_id,
        "email": "dummy@example.com",
        "username": "dummy",
        "role": "user"
    }
    access = create_access_token(token_data, timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    refresh = create_refresh_token(token_data)
    return TokenResponse(
        access=access,
        refresh=refresh
    )


# -----------------------------
# PASSWORD RESET
# -----------------------------
async def password_reset(payload: PasswordResetRequest, db: AsyncSession = Depends(get_db)):
    # TODO: generate reset token, email link to user
    return {"message": "Password reset link sent"}


async def password_reset_confirm(payload: PasswordResetConfirmRequest, db: AsyncSession = Depends(get_db)):
    # TODO: verify reset token, update hashed password in DB
    return {"message": "Password reset successful"}

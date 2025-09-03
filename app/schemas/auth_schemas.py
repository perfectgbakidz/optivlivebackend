from pydantic import BaseModel, EmailStr
from typing import Optional


# -----------------------------
# Requests
# -----------------------------

class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    email: EmailStr
    username: str
    password: str
    first_name: str
    last_name: str
    referral_code: Optional[str] = None


class TwoFAVerifyRequest(BaseModel):
    user_id: str
    token: str


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirmRequest(BaseModel):
    token: str
    new_password: str


# -----------------------------
# Responses
# -----------------------------

class TokenResponse(BaseModel):
    access: str
    refresh: str


class TwoFARequiredResponse(BaseModel):
    two_factor_required: bool = True
    user_id: str

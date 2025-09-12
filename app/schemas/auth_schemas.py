from pydantic import BaseModel, EmailStr, Field
from typing import Optional


# -----------------------------
# Requests
# -----------------------------

class LoginRequest(BaseModel):
    email: EmailStr
    password: str


# 🚀 NEW → Step 1: Initiate Registration (before payment)
class InitiateRegistrationRequest(BaseModel):
    first_name: str = Field(..., alias="firstName")
    last_name: str = Field(..., alias="lastName")
    username: str
    email: EmailStr
    password: str
    referred_by_code: Optional[str] = Field(None, alias="referredByCode")  # 👈 updated

    class Config:
        populate_by_name = True   # allow both snake_case & camelCase


# ✅ Legacy RegisterRequest (if still used elsewhere)
class RegisterRequest(BaseModel):
    email: EmailStr
    username: str
    password: str
    first_name: str
    last_name: str
    referred_by_code: Optional[str] = None  # 👈 updated


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


# 🚀 NEW → Step 1 Response (return Stripe client_secret)
class InitiateRegistrationResponse(BaseModel):
    client_secret: str = Field(..., alias="clientSecret")

    class Config:
        populate_by_name = True

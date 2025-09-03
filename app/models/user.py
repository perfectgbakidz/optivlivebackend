from pydantic import BaseModel, EmailStr
from typing import Optional, Literal
from datetime import datetime
from uuid import UUID


class User(BaseModel):
    id: UUID
    email: EmailStr
    username: str
    first_name: str
    last_name: str
    referral_code: str
    referred_by_code: Optional[str] = None   # changed from UUID → referral_code
    is_kyc_verified: bool = False
    is_2fa_enabled: bool = False
    has_pin: bool = False
    role: Literal["user", "admin"] = "user"
    status: Literal["active", "frozen"] = "active"
    withdrawal_status: Literal["active", "paused"] = "active"
    balance: str = "0.00"  # API will always expose balance as string
    created_at: datetime
    updated_at: datetime


class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str
    first_name: str
    last_name: str
    referral_code: Optional[str] = None  # referral code used at signup (if any)


class UserUpdate(BaseModel):
    first_name: Optional[str]
    last_name: Optional[str]


class UserInDB(User):
    password_hash: str
    withdrawal_pin_hash: Optional[str] = None
    two_fa_secret: Optional[str] = None

from pydantic import BaseModel, EmailStr
from typing import Optional, Literal
from datetime import datetime


# -----------------------------
# Requests
# -----------------------------

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str


class SetPinRequest(BaseModel):
    pin: str


class ChangePinRequest(BaseModel):
    current_password: str
    new_pin: str


class VerifyPinRequest(BaseModel):
    pin: str


class UserUpdateRequest(BaseModel):
    first_name: Optional[str]
    last_name: Optional[str]


class WithdrawalRequest(BaseModel):
    amount: float
    currency: str


# -----------------------------
# Responses
# -----------------------------

class UserProfileResponse(BaseModel):
    id: str
    email: EmailStr
    username: str
    first_name: str
    last_name: str
    referral_code: str                  # the user’s own referral code
    referred_by_code: Optional[str]     # referral code of the referrer (e.g., "MASTERKEY")
    is_kyc_verified: bool
    balance: str
    has_pin: bool
    is2fa_enabled: bool
    role: Literal["user", "admin"]
    status: Literal["active", "frozen"]
    withdrawal_status: Literal["active", "paused"]


class WithdrawalResponse(BaseModel):
    id: str
    amount: str
    currency: str
    status: Literal["pending", "approved", "rejected"]
    requested_at: datetime


class TransactionResponse(BaseModel):
    id: str
    type: str
    amount: str
    currency: str
    status: str
    reference: Optional[str]
    created_at: datetime
    user_id: Optional[str]
    referee_id: Optional[str]
    tier: Optional[int]
    note: Optional[str]

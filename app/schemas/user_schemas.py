from pydantic import BaseModel, EmailStr
from typing import Optional, Literal


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
    referred_by_code: Optional[str]     # NEW → referral code of the referrer (e.g., "MASTERKEY")
    is_kyc_verified: bool
    balance: str
    has_pin: bool
    is2fa_enabled: bool
    role: Literal["user", "admin"]
    status: Literal["active", "frozen"]
    withdrawal_status: Literal["active", "paused"]

from datetime import datetime
from pydantic import BaseModel, EmailStr, Field
from typing import Literal, Optional


# -----------------------------
# Responses
# -----------------------------
class AdminStatsResponse(BaseModel):
    total_users: int
    total_user_referral_earnings: str
    admin_referral_earnings: str
    pending_withdrawals_count: int
    protocol_balance: str


class AdminUserResponse(BaseModel):
    id: str
    email: str
    username: str
    role: Literal["user", "admin"]
    status: Literal["active", "frozen"]
    withdrawal_status: Literal["active", "paused"]
    is_kyc_verified: bool
    balance: str


# -----------------------------
# Requests
# -----------------------------
class AdminUserCreateRequest(BaseModel):
    first_name: str = Field(..., alias="firstName")
    last_name: str = Field(..., alias="lastName")
    email: EmailStr
    username: str
    password: str   # default password provided by admin
    referral_code: Optional[str] = Field(None, alias="referralCode")

    class Config:
        populate_by_name = True   # ✅ allows both snake_case & camelCase


class AdminKYCResponse(BaseModel):
    id: str
    dateSubmitted: datetime
    userName: str
    userEmail: str
    address: Optional[str]
    city: Optional[str]
    postalCode: Optional[str]
    country: Optional[str]
    documentUrl: Optional[str]   # front_url (extend later if you want back_url too)
    status: Literal["pending", "approved", "rejected"]

    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    notes: Optional[str] = None

class AdminKYCProcessRequest(BaseModel):
    decision: Literal["approved", "rejected"]
    rejection_reason: Optional[str] = None

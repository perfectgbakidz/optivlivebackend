from pydantic import BaseModel, EmailStr
from typing import Optional, List


# ---------- User Schemas ----------

class UserBase(BaseModel):
    username: str
    email: EmailStr


class UserCreate(UserBase):
    password: str
    referral_code: Optional[str]  # optional if admin creates, required if user registers


class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    role: Optional[str] = None  # allow admin to update role


class UserResponse(UserBase):
    id: int
    referral_code: Optional[str] = None
    parent_referral: Optional[str] = None
    role: str

    # ✅ Added fields the frontend expects
    is_kyc_verified: bool = False
    balance: str = "0.00"  # keep as string for consistency
    firstName: Optional[str] = None
    lastName: Optional[str] = None

    class Config:
        from_attributes = True


# ---------- Auth Schemas ----------

class Login(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access: str              # 🔑 frontend expects "access", not "access_token"
    refresh: Optional[str]   # frontend expects this field
    role: str                # include role so frontend knows if admin/user immediately


# ---------- Team / Referrals ----------

class TeamMember(BaseModel):
    id: int
    username: str
    email: EmailStr
    referral_code: str

    class Config:
        from_attributes = True


class ReferralAnalytics(BaseModel):
    total_referrals: int
    active_referrals: int
    pending_referrals: int
    conversion_rate: float


class ReferralListResponse(BaseModel):
    total: int
    page: int
    size: int
    referrals: List[TeamMember]


# ---------- Withdrawals ----------

class WithdrawalBase(BaseModel):
    amount: str
    bank_name: str
    account_number: str
    account_name: str


class WithdrawalCreate(WithdrawalBase):
    pass


class WithdrawalResponse(WithdrawalBase):
    id: int
    status: str
    user_id: int

    class Config:
        from_attributes = True


# ---------- KYC ----------

class KycRequestBase(BaseModel):
    address: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    document_url: Optional[str] = None


class KycRequestCreate(KycRequestBase):
    pass


class KycRequestResponse(KycRequestBase):
    id: int
    user_id: int
    status: str

    class Config:
        from_attributes = True


class KycProcessRequest(BaseModel):
    userId: int
    action: str   # "approve" or "reject"
    reason: Optional[str] = None


# ---------- Admin Stats ----------

class AdminStats(BaseModel):
    total_users: int
    total_user_referral_earnings: float
    pending_withdrawals_count: int
    protocol_balance: float


# ---------- Transactions ----------

class TransactionResponse(BaseModel):
    id: int
    user_id: int
    type: str          # e.g., "deposit", "withdrawal", "referral_bonus"
    amount: str
    status: str
    created_at: str    # assuming stored as string/datetime

    class Config:
        from_attributes = True

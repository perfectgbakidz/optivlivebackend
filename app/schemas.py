from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime


# ---------- User Schemas ----------

class UserBase(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone: Optional[str] = None


class UserCreate(UserBase):
    password: str
    referral_code: Optional[str] = None
    role: str = "user"


class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None


class UserResponse(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: EmailStr
    phone: Optional[str] = None
    referral_code: str
    referred_by: Optional[int] = None
    role: str

    # ✅ Frontend expects these
    is_kyc_verified: bool = False
    balance: float = 0.00
    hasPin: bool = False
    is2faEnabled: bool = False

    # ✅ Admin control fields
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


# ---------- Profile Update ----------

class UserProfileUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None


# ---------- Auth Schemas ----------

class Login(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access: str
    refresh: Optional[str]
    role: str


# ---------- Password Change ----------

class PasswordChangeRequest(BaseModel):
    old_password: str
    new_password: str


# ---------- PIN ----------

class PinSetRequest(BaseModel):
    pin: str


class PinVerifyResponse(BaseModel):
    verified: bool


# ---------- Team / Referrals ----------

class TeamMember(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: EmailStr
    referral_code: str
    children: List["TeamMember"] = Field(default_factory=list)

    class Config:
        from_attributes = True


# ---------- Withdrawals ----------

class WithdrawalBase(BaseModel):
    amount: float
    bank_name: str
    account_number: str
    account_name: str


class WithdrawalCreate(WithdrawalBase):
    pass


class WithdrawalResponse(BaseModel):
    id: int
    user_id: int
    amount: float
    bank_name: str
    account_number: str
    account_name: str
    status: str
    date: datetime = Field(..., alias="created_at")

    class Config:
        from_attributes = True
        populate_by_name = True


class WithdrawalDenyRequest(BaseModel):
    reason: Optional[str] = None


# ---------- KYC ----------

class KycRequestBase(BaseModel):
    address: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    document_url: Optional[str] = None


class KycRequestCreate(KycRequestBase):
    pass


class KycRequestResponse(BaseModel):
    id: int
    userId: int = Field(..., alias="user_id")
    first_name: str = Field(..., alias="user.first_name")
    last_name: str = Field(..., alias="user.last_name")
    userEmail: str = Field(..., alias="user.email")
    dateSubmitted: datetime = Field(..., alias="created_at")
    address: Optional[str] = None
    city: Optional[str] = None
    postalCode: Optional[str] = Field(None, alias="postal_code")
    country: Optional[str] = None
    documentUrl: Optional[str] = Field(None, alias="document_url")
    status: str
    rejection_reason: Optional[str] = None

    class Config:
        from_attributes = True
        populate_by_name = True


class KycProcessRequest(BaseModel):
    action: str   # "approve" or "reject"
    reason: Optional[str] = None


# ---------- Admin Stats ----------

class AdminStats(BaseModel):
    totalUsers: int
    totalUserReferralEarnings: float
    pendingWithdrawalsCount: int
    protocolBalance: float


# ---------- Transactions ----------

class TransactionUser(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr


class TransactionResponse(BaseModel):
    id: int
    user_id: int
    type: str
    amount: float
    status: str
    created_at: datetime
    user: TransactionUser

    class Config:
        from_attributes = True

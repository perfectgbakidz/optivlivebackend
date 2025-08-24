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
    refresh: Optional[str]   # placeholder, can implement refresh later
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

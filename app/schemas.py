from pydantic import BaseModel, EmailStr
from typing import Optional

class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    password: str
    referral_code: Optional[str]  # must provide unless admin creates

class UserResponse(UserBase):
    id: int
    referral_code: str
    parent_referral: Optional[str]
    role: str

    class Config:
        from_attributes = True

class Login(BaseModel):
    email: EmailStr
    password: str

class TeamMember(BaseModel):
    id: int
    username: str
    email: EmailStr
    referral_code: str

    class Config:
        from_attributes = True

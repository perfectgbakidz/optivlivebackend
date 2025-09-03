from pydantic import BaseModel
from typing import Literal
from datetime import datetime
from uuid import UUID


class Transaction(BaseModel):
    id: UUID
    user_id: UUID
    type: Literal["deposit", "withdrawal", "referral_bonus", "admin_credit"]
    amount: str
    currency: str = "GBP"
    status: Literal["pending", "completed", "failed"] = "pending"
    reference: str
    created_at: datetime


class TransactionCreate(BaseModel):
    type: Literal["deposit", "withdrawal", "referral_bonus", "admin_credit"]
    amount: str
    currency: str = "GBP"
    reference: str

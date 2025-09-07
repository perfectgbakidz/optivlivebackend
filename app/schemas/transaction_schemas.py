from pydantic import BaseModel
from typing import Literal, Optional
from datetime import datetime


# -----------------------------
# Responses
# -----------------------------
class TransactionResponse(BaseModel):
    id: str
    type: Literal["deposit", "withdrawal", "referral_bonus", "admin_credit"]
    amount: str
    currency: str
    status: Literal["pending", "completed", "failed"]
    reference: str
    created_at: datetime

    # Optional fields for richer context
    user_id: Optional[str] = None
    referee_id: Optional[str] = None
    tier: Optional[int] = None
    note: Optional[str] = None

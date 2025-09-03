from pydantic import BaseModel
from typing import Literal, Optional
from datetime import datetime
from uuid import UUID


class Withdrawal(BaseModel):
    id: UUID
    user_id: UUID
    amount: str
    destination_address: str
    status: Literal["pending", "approved", "denied"] = "pending"
    admin_id: Optional[UUID] = None
    requested_at: datetime
    processed_at: Optional[datetime] = None


class WithdrawalCreate(BaseModel):
    amount: str
    destination_address: str

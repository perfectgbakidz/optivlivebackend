from pydantic import BaseModel
from typing import Literal
from datetime import datetime


# -----------------------------
# Requests
# -----------------------------

class WithdrawalCreateRequest(BaseModel):
    amount: str
    destination_address: str


# -----------------------------
# Responses
# -----------------------------

class WithdrawalResponse(BaseModel):
    id: str
    amount: str
    destination_address: str
    status: Literal["pending", "approved", "denied"]
    requested_at: datetime
    processed_at: datetime | None = None

from pydantic import BaseModel
from datetime import datetime
from uuid import UUID


class ReferralEarning(BaseModel):
    id: UUID
    user_id: UUID            # the one who received the bonus
    referee_id: UUID         # the one who triggered it
    amount: str
    created_at: datetime


class ReferralCreate(BaseModel):
    user_id: UUID
    referee_id: UUID
    amount: str

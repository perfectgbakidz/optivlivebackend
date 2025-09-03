from pydantic import BaseModel
from typing import Optional, Literal
from datetime import datetime
from uuid import UUID


class KYC(BaseModel):
    id: UUID
    user_id: UUID
    document_type: str
    document_front_url: str
    document_back_url: Optional[str] = None
    status: Literal["pending", "approved", "rejected"] = "pending"
    reviewed_by: Optional[UUID] = None
    submitted_at: datetime
    reviewed_at: Optional[datetime] = None


class KYCSubmit(BaseModel):
    document_type: str
    document_front_url: str
    document_back_url: Optional[str] = None

from pydantic import BaseModel
from typing import Optional, Literal


# -----------------------------
# Requests
# -----------------------------
class KYCSubmitRequest(BaseModel):
    document_type: str
    address: str
    city: str
    postal_code: str
    country: str
    document_front_url: str
    document_back_url: Optional[str] = None
    selfie_url: Optional[str] = None


# -----------------------------
# Responses
# -----------------------------
class KYCStatusResponse(BaseModel):
    status: Literal["pending", "approved", "rejected", "not_submitted"]
    rejection_reason: Optional[str] = None

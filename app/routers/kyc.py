from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
import shutil
import uuid
import os

from .. import models, schemas, database, auth

router = APIRouter(prefix="/kyc", tags=["KYC"])

# Folder for storing uploaded documents (you can move this to S3, Cloudinary, etc.)
UPLOAD_DIR = "uploads/kyc"
os.makedirs(UPLOAD_DIR, exist_ok=True)


# --------------------------
# Submit KYC documents
# --------------------------
@router.post("/submit/", response_model=schemas.KycRequestResponse)
async def submit_kyc(
    document_type: str = Form(...),   # e.g., "passport", "id_card"
    document_front: UploadFile = File(...),
    document_back: Optional[UploadFile] = File(None),
    selfie: Optional[UploadFile] = File(None),
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    # Save files to uploads folder with unique names
    def save_file(file: UploadFile, prefix: str) -> str:
        ext = os.path.splitext(file.filename)[1]
        filename = f"{prefix}_{uuid.uuid4().hex}{ext}"
        filepath = os.path.join(UPLOAD_DIR, filename)
        with open(filepath, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        return filepath

    document_urls = []
    if document_front:
        document_urls.append(save_file(document_front, "front"))
    if document_back:
        document_urls.append(save_file(document_back, "back"))
    if selfie:
        document_urls.append(save_file(selfie, "selfie"))

    # Create new KYC request
    kyc_request = models.KycRequest(
        user_id=current_user.id,
        status="pending",
        document_url=",".join(document_urls),  # store multiple files as CSV string
    )
    db.add(kyc_request)
    db.commit()
    db.refresh(kyc_request)

    # Mark user as having submitted KYC
    current_user.is_kyc_verified = False
    db.commit()

    return kyc_request


# --------------------------
# Get KYC status
# --------------------------
@router.get("/status/")
def get_kyc_status(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    kyc = (
        db.query(models.KycRequest)
        .filter(models.KycRequest.user_id == current_user.id)
        .order_by(models.KycRequest.id.desc())
        .first()
    )

    if not kyc:
        return {"status": "unverified", "rejection_reason": None}

    if kyc.status == "rejected":
        return {"status": "rejected", "rejection_reason": getattr(kyc, "rejection_reason", None)}

    return {"status": kyc.status, "rejection_reason": None}

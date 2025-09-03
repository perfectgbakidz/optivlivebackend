from fastapi import APIRouter, Depends, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.kyc_schemas import KYCStatusResponse
from app.services import kyc_service
from app.dependencies import get_current_user
from app.database import get_db

router = APIRouter(prefix="/kyc", tags=["KYC"])


@router.get("/status/", response_model=KYCStatusResponse)
async def get_kyc_status(
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await kyc_service.get_status(user, db)


@router.post("/submit/")
async def submit_kyc(
    document_type: str = Form(...),
    address: str = Form(...),
    city: str = Form(...),
    postal_code: str = Form(...),
    country: str = Form(...),
    document_front: UploadFile = File(...),
    selfie: UploadFile = File(...),
    document_back: UploadFile | None = File(None),
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await kyc_service.submit(
        user=user,
        document_type=document_type,
        address=address,
        city=city,
        postal_code=postal_code,
        country=country,
        document_front=document_front,
        selfie=selfie,
        document_back=document_back,
        db=db
    )
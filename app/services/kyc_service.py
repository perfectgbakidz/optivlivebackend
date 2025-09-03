from fastapi import HTTPException, UploadFile, File, Form, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from datetime import datetime
from uuid import uuid4
from typing import Optional
from app.schemas.kyc_schemas import KYCStatusResponse
from app.database import get_db
from app.services.storage_service import upload_to_supabase


# -----------------------------
# GET USER KYC STATUS
# -----------------------------
async def get_status(user, db: AsyncSession) -> KYCStatusResponse:
    query = text("""
        SELECT status 
        FROM kyc 
        WHERE user_id = :uid 
        ORDER BY submitted_at DESC 
        LIMIT 1
    """)
    result = await db.execute(query, {"uid": user["id"]})
    record = result.fetchone()

    if not record:
        return KYCStatusResponse(status="not_submitted")  # Default before any submission

    return KYCStatusResponse(status=record.status)


# -----------------------------
# SUBMIT KYC DOCUMENTS
# -----------------------------
async def submit(
    user,
    document_type: str,
    address: str,
    city: str,
    postal_code: str,
    country: str,
    document_front: UploadFile,
    selfie: UploadFile,
    document_back: Optional[UploadFile] = None,
    db: AsyncSession = None,
):
    # Upload files to Supabase
    front_url = await upload_to_supabase(document_front)
    back_url = await upload_to_supabase(document_back) if document_back else None
    selfie_url = await upload_to_supabase(selfie) if selfie else None

    kid = str(uuid4())
    insert_q = text("""
        INSERT INTO kyc (
            id, user_id, document_type,
            address, city, postal_code, country,
            document_front_url, document_back_url, selfie_url,
            status, submitted_at
        )
        VALUES (:id, :uid, :doctype,
                :address, :city, :postal, :country,
                :front, :back, :selfie,
                'pending', :submitted)
    """)
    await db.execute(insert_q, {
        "id": kid,
        "uid": user["id"],
        "doctype": document_type,
        "address": address,
        "city": city,
        "postal": postal_code,
        "country": country,
        "front": front_url,
        "back": back_url,
        "selfie": selfie_url,
        "submitted": datetime.utcnow(),
    })
    await db.commit()

    return {
        "message": "KYC submitted successfully",
        "kyc_id": kid,
        "front_url": front_url,
        "back_url": back_url,
        "selfie_url": selfie_url,
    }

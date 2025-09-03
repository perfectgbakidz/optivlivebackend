from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.schemas.admin_schemas import AdminStatsResponse, AdminUserResponse, AdminUserCreateRequest, AdminKYCProcessRequest
from app.services import admin_service
from app.dependencies import get_current_admin
from app.database import get_db

router = APIRouter(prefix="/admin", tags=["Admin"])


# -----------------------------
# STATS
# -----------------------------
@router.get("/stats/", response_model=AdminStatsResponse)
async def get_stats(admin=Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    return await admin_service.get_stats(admin, db)


# -----------------------------
# USERS
# -----------------------------
@router.get("/users/", response_model=List[AdminUserResponse])
async def list_users(admin=Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    return await admin_service.list_users(admin, db)


@router.post("/users/")
async def create_user(
    payload: AdminUserCreateRequest,
    admin=Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await admin_service.create_user(admin, payload, db)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# -----------------------------
# KYC
# -----------------------------
@router.get("/kyc/")
async def list_kyc_requests(admin=Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    return await admin_service.list_kyc_requests(admin, db)


@router.post("/kyc/{kyc_id}/process/")
async def process_kyc(
    kyc_id: str,
    payload: AdminKYCProcessRequest,
    admin=Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    return await admin_service.process_kyc(
        admin=admin,
        kyc_id=kyc_id,
        decision=payload.decision,
        rejection_reason=payload.rejection_reason,
        db=db
    )


# -----------------------------
# WITHDRAWALS
# -----------------------------
@router.get("/withdrawals/")
async def list_withdrawals(admin=Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    return await admin_service.list_withdrawals(admin, db)


@router.post("/withdrawals/{withdrawal_id}/approve/")
async def approve_withdrawal(withdrawal_id: str, admin=Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    return await admin_service.approve_withdrawal(admin, withdrawal_id, db)


@router.post("/withdrawals/{withdrawal_id}/deny/")
async def deny_withdrawal(withdrawal_id: str, admin=Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    return await admin_service.deny_withdrawal(admin, withdrawal_id, db)


# -----------------------------
# TRANSACTIONS
# -----------------------------
@router.get("/transactions/")
async def list_all_transactions(admin=Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    return await admin_service.list_transactions(admin, db)

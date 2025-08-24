from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List
from .. import models, schemas, utils, database, auth

router = APIRouter(prefix="/admin", tags=["Admin"])

# --------------------------
# Create User (Admin only)
# --------------------------
@router.post("/users/create/", response_model=schemas.UserResponse)
def create_user(
    user: schemas.UserCreate,
    db: Session = Depends(database.get_db),
    admin=Depends(auth.get_admin_user)
):
    existing = db.query(models.User).filter(models.User.email == user.email).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already exists")

    new_code = utils.generate_unique_referral(db)

    new_user = models.User(
        username=user.username,
        email=user.email,
        password_hash=auth.hash_password(user.password),
        referral_code=new_code,
        parent_referral=user.referral_code if user.referral_code else None,
        role=user.role if user.role else "user"
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


# --------------------------
# Get All Users
# --------------------------
@router.get("/users/", response_model=List[schemas.UserResponse])
def get_all_users(
    db: Session = Depends(database.get_db),
    admin=Depends(auth.get_admin_user)
):
    return db.query(models.User).all()


# --------------------------
# Update User
# --------------------------
@router.patch("/users/{user_id}/", response_model=schemas.UserResponse)
def update_user(
    user_id: int,
    user_update: schemas.UserUpdate,
    db: Session = Depends(database.get_db),
    admin=Depends(auth.get_admin_user)
):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if user_update.username:
        user.username = user_update.username
    if user_update.email:
        existing = db.query(models.User).filter(
            models.User.email == user_update.email, models.User.id != user_id
        ).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already in use")
        user.email = user_update.email
    if user_update.password:
        user.password_hash = auth.hash_password(user_update.password)
    if user_update.role:
        user.role = user_update.role

    db.commit()
    db.refresh(user)
    return user


# --------------------------
# Withdrawals (Admin actions)
# --------------------------
@router.post("/withdrawals/admin/approve/{withdrawal_id}/")
def approve_withdrawal(
    withdrawal_id: int,
    db: Session = Depends(database.get_db),
    admin=Depends(auth.get_admin_user)
):
    withdrawal = db.query(models.Withdrawal).filter(models.Withdrawal.id == withdrawal_id).first()
    if not withdrawal:
        raise HTTPException(status_code=404, detail="Withdrawal not found")
    withdrawal.status = "approved"
    db.commit()
    return {"message": "Withdrawal approved", "status": "approved"}


@router.post("/withdrawals/admin/deny/{withdrawal_id}/")
def deny_withdrawal(
    withdrawal_id: int,
    reason: str,
    db: Session = Depends(database.get_db),
    admin=Depends(auth.get_admin_user)
):
    withdrawal = db.query(models.Withdrawal).filter(models.Withdrawal.id == withdrawal_id).first()
    if not withdrawal:
        raise HTTPException(status_code=404, detail="Withdrawal not found")
    withdrawal.status = "denied"
    db.commit()
    return {"message": "Withdrawal denied", "status": "denied", "reason": reason}


# --------------------------
# KYC (Admin actions)
# --------------------------
@router.get("/kyc/admin/list/", response_model=List[schemas.KycRequestResponse])
def list_kyc_requests(
    db: Session = Depends(database.get_db),
    admin=Depends(auth.get_admin_user)
):
    return db.query(models.KycRequest).all()


@router.post("/kyc/admin/process/")
def process_kyc(
    request: schemas.KycProcessRequest,
    db: Session = Depends(database.get_db),
    admin=Depends(auth.get_admin_user)
):
    kyc = db.query(models.KycRequest).filter(models.KycRequest.id == request.userId).first()
    if not kyc:
        raise HTTPException(status_code=404, detail="KYC request not found")
    kyc.status = "approved" if request.action == "approve" else "rejected"
    db.commit()
    return {"success": True}

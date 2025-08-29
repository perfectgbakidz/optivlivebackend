from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, cast, Float
from typing import List
from .. import models, schemas, utils, database, auth

router = APIRouter(prefix="/admin", tags=["Admin"])


# --------------------------
# Admin Stats
# --------------------------
@router.get("/stats/", response_model=schemas.AdminStats)
def get_admin_stats(
    db: Session = Depends(database.get_db),
    admin=Depends(auth.get_admin_user)
):
    total_users = db.query(models.User).count()
    total_user_referral_earnings = (
        db.query(func.sum(models.User.total_commission)).scalar() or 0
    )
    pending_withdrawals_count = (
        db.query(models.Withdrawal).filter(models.Withdrawal.status == "pending").count()
    )
    protocol_balance = (
        db.query(func.sum(cast(models.User.balance, Float))).scalar() or 0.0
    )

    return {
        "totalUsers": total_users,
        "totalUserReferralEarnings": total_user_referral_earnings,
        "pendingWithdrawalsCount": pending_withdrawals_count,
        "protocolBalance": protocol_balance,
    }


# --------------------------
# Create User (Admin only)
# --------------------------
@router.post("/users/", response_model=schemas.UserResponse)
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

    # ✅ Allow admin to update additional fields
    if hasattr(user_update, "balance") and user_update.balance:
        user.balance = user_update.balance
    if hasattr(user_update, "status") and user_update.status:
        user.status = user_update.status
    if hasattr(user_update, "withdrawalStatus") and user_update.withdrawalStatus:
        user.withdrawalStatus = user_update.withdrawalStatus

    db.commit()
    db.refresh(user)
    return user


# --------------------------
# Withdrawals (Admin actions)
# --------------------------
@router.get("/withdrawals/", response_model=List[schemas.WithdrawalResponse])
def admin_list_withdrawals(
    db: Session = Depends(database.get_db),
    admin=Depends(auth.get_admin_user)
):
    withdrawals = db.query(models.Withdrawal).filter(models.Withdrawal.status == "pending").all()

    # ✅ Mask account number
    for wd in withdrawals:
        if wd.account_number:
            wd.account_number = "****" + wd.account_number[-4:]
    return withdrawals


@router.post("/withdrawals/{withdrawal_id}/approve/")
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
    return {"message": "Withdrawal approved successfully.", "status": "approved"}


@router.post("/withdrawals/{withdrawal_id}/deny/")
def deny_withdrawal(
    withdrawal_id: int,
    request: schemas.WithdrawalDenyRequest,
    db: Session = Depends(database.get_db),
    admin=Depends(auth.get_admin_user)
):
    withdrawal = db.query(models.Withdrawal).filter(models.Withdrawal.id == withdrawal_id).first()
    if not withdrawal:
        raise HTTPException(status_code=404, detail="Withdrawal not found")
    withdrawal.status = "denied"
    db.commit()
    return {"message": "Withdrawal denied.", "status": "denied", "reason": request.reason}


# --------------------------
# KYC (Admin actions)
# --------------------------
@router.get("/kyc/requests/", response_model=List[schemas.KycRequestResponse])
def list_kyc_requests(
    db: Session = Depends(database.get_db),
    admin=Depends(auth.get_admin_user)
):
    kycs = db.query(models.KycRequest).filter(models.KycRequest.status == "pending").all()

    return [
        schemas.KycRequestResponse(
            id=kyc.id,
            userId=kyc.user_id,
            userName=kyc.user.username,
            userEmail=kyc.user.email,
            dateSubmitted=kyc.created_at,
            address=kyc.address,
            city=kyc.city,
            postal_code=kyc.postal_code,
            country=kyc.country,
            documentUrl=kyc.document_url,
            status=kyc.status,
            rejection_reason=kyc.rejection_reason,
        )
        for kyc in kycs
    ]


@router.post("/kyc/process/{id}/")
def process_kyc(
    id: int,
    request: schemas.KycProcessRequest,
    db: Session = Depends(database.get_db),
    admin=Depends(auth.get_admin_user)
):
    kyc = db.query(models.KycRequest).filter(models.KycRequest.id == id).first()
    if not kyc:
        raise HTTPException(status_code=404, detail="KYC request not found")
    kyc.status = "approved" if request.action == "approve" else "rejected"
    if request.action == "reject" and request.reason:
        kyc.rejection_reason = request.reason
    db.commit()
    return {"success": True}


# --------------------------
# Transactions (Admin view)
# --------------------------
@router.get("/transactions/", response_model=List[schemas.TransactionResponse])
def admin_list_transactions(
    db: Session = Depends(database.get_db),
    admin=Depends(auth.get_admin_user)
):
    transactions = db.query(models.Transaction).all()
    return [
        schemas.TransactionResponse(
            id=tx.id,
            user_id=tx.user_id,
            type=tx.type,
            amount=float(tx.amount),
            status=tx.status,
            created_at=tx.created_at,
            user=schemas.TransactionUser(
                name=tx.user.username,
                email=tx.user.email
            ),
        )
        for tx in transactions
    ]

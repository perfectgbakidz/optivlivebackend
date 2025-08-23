from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List
from .. import models, schemas, utils, database, auth

router = APIRouter(prefix="/admin", tags=["Admin"])


# --------------------------
# Create User (Admin only)
# --------------------------
@router.post("/create-user", response_model=schemas.UserResponse)
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
        password_hash=utils.hash_password(user.password),
        referral_code=new_code,
        parent_referral=user.referral_code if user.referral_code else None
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


# --------------------------
# Get All Users
# --------------------------
@router.get("/users", response_model=List[schemas.UserResponse])
def get_all_users(
    db: Session = Depends(database.get_db),
    admin=Depends(auth.get_admin_user)
):
    return db.query(models.User).all()


# --------------------------
# Get Single User by ID
# --------------------------
@router.get("/users/{user_id}", response_model=schemas.UserResponse)
def get_user_by_id(
    user_id: int,
    db: Session = Depends(database.get_db),
    admin=Depends(auth.get_admin_user)
):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


# --------------------------
# Update User
# --------------------------
@router.put("/users/{user_id}", response_model=schemas.UserResponse)
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
        # Ensure email is unique
        existing = db.query(models.User).filter(
            models.User.email == user_update.email, models.User.id != user_id
        ).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already in use")
        user.email = user_update.email
    if user_update.password:
        user.password_hash = utils.hash_password(user_update.password)

    db.commit()
    db.refresh(user)
    return user


# --------------------------
# Delete User
# --------------------------
@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    db: Session = Depends(database.get_db),
    admin=Depends(auth.get_admin_user)
):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    db.delete(user)
    db.commit()
    return None


# --------------------------
# Referral Analytics (Admin only)
# --------------------------
@router.get("/referrals/analytics", response_model=schemas.ReferralAnalytics)
def referral_analytics(
    db: Session = Depends(database.get_db),
    admin=Depends(auth.get_admin_user)
):
    total_users = db.query(models.User).count()
    total_referrals = db.query(models.User).filter(models.User.parent_referral.isnot(None)).count()
    top_referrer = (
        db.query(models.User.username, db.func.count(models.User.id).label("ref_count"))
        .join(models.User, models.User.parent_referral == models.User.referral_code, isouter=True)
        .group_by(models.User.username)
        .order_by(db.desc("ref_count"))
        .first()
    )

    return schemas.ReferralAnalytics(
        total_users=total_users,
        total_referrals=total_referrals,
        top_referrer=top_referrer[0] if top_referrer else None,
        top_referrals=top_referrer[1] if top_referrer else 0,
    )


# --------------------------
# Referral List (Admin only)
# --------------------------
@router.get("/referrals/list", response_model=List[schemas.ReferralListResponse])
def referral_list(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1),
    db: Session = Depends(database.get_db),
    admin=Depends(auth.get_admin_user)
):
    users = db.query(models.User).offset(skip).limit(limit).all()

    response = []
    for user in users:
        response.append(
            schemas.ReferralListResponse(
                id=user.id,
                username=user.username,
                email=user.email,
                referral_code=user.referral_code,
                referred_count=len(user.referrals)
            )
        )
    return response

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from .. import models, schemas, database, auth
from ..utils import verify_password, hash_password  # ✅ password helpers

router = APIRouter(prefix="/users", tags=["Users"])


# --------------------------
# Debug: Get Current User
# --------------------------
@router.get("/me", response_model=schemas.UserResponse)
def get_me(current_user: models.User = Depends(auth.get_current_user)):
    return current_user


# --------------------------
# Get Profile (frontend expects this)
# --------------------------
@router.get("/profile/", response_model=schemas.UserResponse)
def get_profile(current_user: models.User = Depends(auth.get_current_user)):
    return current_user


# --------------------------
# Update Profile (firstName, lastName only)
# --------------------------
@router.patch("/profile/", response_model=schemas.UserResponse)
def update_profile(
    update_data: schemas.UserProfileUpdate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    if update_data.firstName is not None:
        current_user.firstName = update_data.firstName
    if update_data.lastName is not None:
        current_user.lastName = update_data.lastName

    db.commit()
    db.refresh(current_user)
    return current_user


# --------------------------
# Change Password
# --------------------------
@router.post("/password/change/")
def change_password(
    data: schemas.PasswordChangeRequest,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    if not verify_password(data.old_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Old password is incorrect"
        )

    current_user.password_hash = hash_password(data.new_password)
    db.commit()
    return {"detail": "Password updated successfully"}


# --------------------------
# Set Withdrawal PIN
# --------------------------
@router.post("/pin/set/")
def set_pin(
    data: schemas.PinSetRequest,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    current_user.pin_hash = hash_password(data.pin)
    current_user.hasPin = True   # ✅ mark that pin is set
    db.commit()
    return {"detail": "PIN set successfully"}


# --------------------------
# Verify Withdrawal PIN
# --------------------------
@router.post("/pin/verify/", response_model=schemas.PinVerifyResponse)
def verify_pin(
    data: schemas.PinSetRequest,
    current_user: models.User = Depends(auth.get_current_user)
):
    if not current_user.pin_hash or not verify_password(data.pin, current_user.pin_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid PIN"
        )
    return {"verified": True}   # ✅ matches frontend expectation


# --------------------------
# Get Direct Referrals (Team)
# --------------------------
@router.get("/team", response_model=List[schemas.TeamMember])
def get_team(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    team = db.query(models.User).filter(
        models.User.parent_referral == current_user.referral_code
    ).all()
    return team

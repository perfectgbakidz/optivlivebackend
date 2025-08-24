from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from .. import models, schemas, database, auth

router = APIRouter(prefix="/users", tags=["Users"])

# --------------------------
# Get Current User (old endpoint)
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
# Get Team
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

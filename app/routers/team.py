from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from .. import models, schemas, database, auth

router = APIRouter(prefix="/team", tags=["Team"])


# --------------------------
# Recursive helper to build team tree
# --------------------------
def build_team_tree(user: models.User, db: Session) -> schemas.TeamMember:
    children = (
        db.query(models.User)
        .filter(models.User.parent_referral == user.referral_code)
        .all()
    )

    return schemas.TeamMember(
        id=user.id,
        username=user.username,
        email=user.email,
        referral_code=user.referral_code,
        children=[build_team_tree(child, db) for child in children]
    )


# --------------------------
# Get Team Tree
# --------------------------
@router.get("/tree/", response_model=schemas.TeamMember)
def get_team_tree(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """
    Returns the team hierarchy as a tree structure.
    The frontend expects each user to have a `children` array.
    """

    return build_team_tree(current_user, db)

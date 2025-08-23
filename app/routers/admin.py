from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import models, schemas, utils, database, auth

router = APIRouter(prefix="/admin", tags=["Admin"])

@router.post("/create-user", response_model=schemas.UserResponse)
def create_user(user: schemas.UserCreate, db: Session = Depends(database.get_db), admin=Depends(auth.get_admin_user)):
    existing = db.query(models.User).filter(models.User.email == user.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="User already exists")

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

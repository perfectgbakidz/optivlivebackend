from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import schemas, models, utils, database, auth

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=schemas.UserResponse)
def register(user: schemas.UserCreate, db: Session = Depends(database.get_db)):
    referrer = db.query(models.User).filter(models.User.referral_code == user.referral_code).first()
    if not referrer:
        raise HTTPException(status_code=400, detail="Invalid referral code")

    existing = db.query(models.User).filter(
        (models.User.email == user.email) | (models.User.username == user.username)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="User already exists")

    # generate unique referral code
    new_code = utils.generate_unique_referral(db)

    new_user = models.User(
        username=user.username,
        email=user.email,
        password_hash=utils.hash_password(user.password),
        referral_code=new_code,
        parent_referral=user.referral_code
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@router.post("/login")
def login(user: schemas.Login, db: Session = Depends(database.get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if not db_user or not utils.verify_password(user.password, db_user.password_hash):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    token = auth.create_access_token({"sub": db_user.email})
    return {"access_token": token, "token_type": "bearer"}

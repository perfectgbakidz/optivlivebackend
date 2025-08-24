from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta
from .. import schemas, models, utils, database, auth

router = APIRouter(prefix="/auth", tags=["Authentication"])


# --------------------------
# Register User
# --------------------------
@router.post("/register", response_model=schemas.UserResponse)
def register(user: schemas.UserCreate, db: Session = Depends(database.get_db)):
    if not user.referral_code:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Referral code is required")

    referrer = db.query(models.User).filter(models.User.referral_code == user.referral_code).first()
    if not referrer:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid referral code")

    existing = db.query(models.User).filter(
        (models.User.email == user.email) | (models.User.username == user.username)
    ).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already exists")

    new_code = utils.generate_unique_referral(db)

    new_user = models.User(
        username=user.username,
        email=user.email,
        password_hash=auth.hash_password(user.password),
        referral_code=new_code,
        parent_referral=user.referral_code,
        role="user"
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


# --------------------------
# Login
# --------------------------
@router.post("/login")
def login(user: schemas.Login, db: Session = Depends(database.get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if not db_user or not auth.verify_password(user.password, db_user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    # Short-lived access token
    access_token = auth.create_access_token(
        {"sub": db_user.email, "role": db_user.role},
        expires_delta=timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    # Longer-lived refresh token
    refresh_token = auth.create_access_token(
        {"sub": db_user.email, "role": db_user.role},
        expires_delta=timedelta(days=7)
    )

    return {
        "access": access_token,   # ✅ what frontend expects
        "refresh": refresh_token, # ✅ matches frontend
        "role": db_user.role
    }


# --------------------------
# Get Current User
# --------------------------
@router.get("/me", response_model=schemas.UserResponse)
def get_me(current_user: models.User = Depends(auth.get_current_user)):
    return current_user

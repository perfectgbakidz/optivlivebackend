from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import models, database
from app.auth import hash_password

router = APIRouter()

@router.post("/create-admin")
def create_admin(db: Session = Depends(database.get_db)):
    email = "admin@optivus.com"
    username = "admin"
    password = "StrongPassword123"
    hashed_pw = hash_password(password)

    # Check if admin already exists
    existing_admin = db.query(models.User).filter(models.User.role == "admin").first()
    if existing_admin:
        raise HTTPException(status_code=400, detail="Admin already exists")

    admin_user = models.User(
        username=username,
        email=email,
        password_hash=hashed_pw,
        role="admin",
        referral_code=None  # ✅ no referral for admin
    )
    db.add(admin_user)
    db.commit()
    db.refresh(admin_user)

    return {
        "msg": "Admin created successfully",
        "email": email,
        "username": username,
        "password": password  # return once so you can log in
    }

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app import models, database
from app.auth import hash_password

router = APIRouter()

@router.post("/create-admin")
def create_admin(db: Session = Depends(database.get_db)):
    email = "admin@optivus.com"
    password = "StrongPassword123"
    hashed_pw = hash_password(password)

    admin_user = models.User(email=email, hashed_password=hashed_pw, role="admin")
    db.add(admin_user)
    db.commit()
    return {"msg": "Admin created", "email": email, "password": password}

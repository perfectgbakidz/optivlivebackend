import random, string
from sqlalchemy.orm import Session
from . import models

def generate_referral_code(length: int = 6) -> str:
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

def generate_unique_referral(db: Session) -> str:
    code = generate_referral_code()
    while db.query(models.User).filter(models.User.referral_code == code).first():
        code = generate_referral_code()
    return code

import bcrypt

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

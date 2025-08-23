import random
import string
import bcrypt
from sqlalchemy.orm import Session
from sqlalchemy import func
from . import models


# ---------------------------
# Referral Code Generators
# ---------------------------
def generate_referral_code(length: int = 6) -> str:
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))


def generate_unique_referral(db: Session) -> str:
    code = generate_referral_code()
    while db.query(models.User).filter(models.User.referral_code == code).first():
        code = generate_referral_code()
    return code


# ---------------------------
# Password Hashing
# ---------------------------
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))


# ---------------------------
# Referral Analytics Helpers
# ---------------------------
def get_referral_clicks(db: Session, referral_code: str) -> int:
    """
    Returns total number of clicks recorded for a referral code.
    Requires a ReferralClick model/table to exist.
    """
    return db.query(func.count(models.ReferralClick.id)).filter(
        models.ReferralClick.referral_code == referral_code
    ).scalar() or 0


def get_total_signups(db: Session, referral_code: str) -> int:
    """
    Returns total number of users signed up with this referral code as parent_referral.
    """
    return db.query(func.count(models.User.id)).filter(
        models.User.parent_referral == referral_code
    ).scalar() or 0


def get_conversion_rate(db: Session, referral_code: str) -> float:
    """
    Returns conversion rate = (signups / clicks) * 100
    """
    clicks = get_referral_clicks(db, referral_code)
    signups = get_total_signups(db, referral_code)
    if clicks == 0:
        return 0.0
    return (signups / clicks) * 100

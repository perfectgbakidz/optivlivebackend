from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint, Float, Boolean
from sqlalchemy.orm import relationship
from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)

    # Each user has a unique referral code
    referral_code = Column(String, unique=True, index=True, nullable=True)

    # Parent referral must point to another user's referral code
    parent_referral = Column(String, ForeignKey("users.referral_code"), nullable=True)

    role = Column(String, default="user")  # "user" or "admin"

    # ✅ New fields the frontend expects
    is_kyc_verified = Column(Boolean, default=False)
    balance = Column(String, default="0.00")  # stored as string for consistency with frontend
    firstName = Column(String, nullable=True)
    lastName = Column(String, nullable=True)

    # Relationship to see who was referred by this user
    referrals = relationship(
        "User",
        backref="referrer",
        remote_side=[referral_code]
    )

    # Referral analytics fields
    referral_clicks = Column(Integer, default=0)   # how many times their link was clicked
    referral_signups = Column(Integer, default=0)  # how many registered via their link
    total_commission = Column(Float, default=0.0)  # total commission earned

    # Explicit unique constraint for Postgres foreign key
    __table_args__ = (
        UniqueConstraint("referral_code", name="uq_users_referral_code"),
    )

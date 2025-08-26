from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint, Float, Boolean, DateTime, func
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

    # ✅ Fields required by frontend
    is_kyc_verified = Column(Boolean, default=False)
    balance = Column(String, default="0.00")  # keep as string for consistency
    firstName = Column(String, nullable=True)
    lastName = Column(String, nullable=True)
    hasPin = Column(Boolean, default=False)
    pin_hash = Column(String, nullable=True)
    is2faEnabled = Column(Boolean, default=False)

    # Referral tracking
    referrals = relationship(
        "User",
        backref="referrer",
        remote_side=[referral_code]
    )
    referral_clicks = Column(Integer, default=0)
    referral_signups = Column(Integer, default=0)
    total_commission = Column(Float, default=0.0)

    # Relationships
    withdrawals = relationship("Withdrawal", back_populates="user", cascade="all, delete-orphan")
    kyc_requests = relationship("KycRequest", back_populates="user", cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="user", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("referral_code", name="uq_users_referral_code"),
    )


class Withdrawal(Base):
    __tablename__ = "withdrawals"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Amounts
    amount = Column(String, nullable=False)       # amount user receives (after fees)
    fee = Column(String, default="0.00")          # fee charged

    # Bank details
    bank_name = Column(String, nullable=False)
    account_number = Column(String, nullable=False)
    account_name = Column(String, nullable=False)

    status = Column(String, default="pending")    # pending | approved | denied | paid

    user = relationship("User", back_populates="withdrawals")


class KycRequest(Base):
    __tablename__ = "kyc_requests"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(String, default="pending")  # pending | approved | rejected
    document_url = Column(String, nullable=True)
    rejection_reason = Column(String, nullable=True)  # ✅ added for admin rejection

    # Extra details
    address = Column(String, nullable=True)
    city = Column(String, nullable=True)
    postal_code = Column(String, nullable=True)
    country = Column(String, nullable=True)

    user = relationship("User", back_populates="kyc_requests")


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    type = Column(String, nullable=False)   # withdrawal | deposit | commission | etc
    reference = Column(String, nullable=True)  # ✅ description / tracking reference
    amount = Column(String, nullable=False)    # keep as string for consistency
    status = Column(String, default="pending")  # pending | completed | failed
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="transactions")

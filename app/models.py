# app/models.py

from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, ForeignKey, Float, Text, Enum
)
from sqlalchemy.orm import relationship, declarative_base
import enum

Base = declarative_base()


# -------------------------
# ENUMS
# -------------------------
class UserRole(str, enum.Enum):
    user = "user"
    admin = "admin"


class KYCStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class TransactionType(str, enum.Enum):
    deposit = "deposit"
    withdrawal = "withdrawal"
    referral_bonus = "referral_bonus"


class TransactionStatus(str, enum.Enum):
    pending = "pending"
    confirmed = "confirmed"
    failed = "failed"


class WithdrawalStatus(str, enum.Enum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    rejected = "rejected"


# -------------------------
# MODELS
# -------------------------
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    phone_number = Column(String, unique=True, index=True)
    role = Column(Enum(UserRole), default=UserRole.user, nullable=False)
    referral_code = Column(String, unique=True, nullable=True)
    referred_by = Column(String, ForeignKey("users.referral_code"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    pin_hash = Column(String, nullable=True)

    # Relationships
    referrals = relationship("User", remote_side=[referral_code])
    kyc = relationship("KYC", back_populates="user", uselist=False)
    transactions = relationship("Transaction", back_populates="user")
    withdrawals = relationship("Withdrawal", back_populates="user")


class KYC(Base):
    __tablename__ = "kyc"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    document_type = Column(String, nullable=False)  # e.g., "passport", "id_card"
    document_number = Column(String, nullable=False)
    document_file = Column(String, nullable=False)  # path in uploads/kyc/
    status = Column(Enum(KYCStatus), default=KYCStatus.pending, nullable=False)
    submitted_at = Column(DateTime, default=datetime.utcnow)
    reviewed_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="kyc")


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    amount = Column(Float, nullable=False)
    type = Column(Enum(TransactionType), nullable=False)
    status = Column(Enum(TransactionStatus), default=TransactionStatus.pending, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    reference = Column(String, unique=True, nullable=False)

    # Relationships
    user = relationship("User", back_populates="transactions")


class Withdrawal(Base):
    __tablename__ = "withdrawals"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    amount = Column(Float, nullable=False)
    status = Column(Enum(WithdrawalStatus), default=WithdrawalStatus.pending, nullable=False)
    requested_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)
    tx_hash = Column(String, nullable=True)  # blockchain/transaction hash for tracking

    # Relationships
    user = relationship("User", back_populates="withdrawals")

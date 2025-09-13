from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from datetime import datetime
from typing import List
from uuid import uuid4
import secrets

from app.schemas.admin_schemas import AdminStatsResponse, AdminUserResponse, AdminUserCreateRequest
from app.utils.security import hash_password


# -----------------------------
# ADMIN DASHBOARD STATS
# -----------------------------
async def get_stats(admin, db: AsyncSession) -> AdminStatsResponse:
    res_users = await db.execute(text("SELECT COUNT(*) FROM users"))
    total_users = res_users.scalar() or 0

    res_ref = await db.execute(
        text("SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE type = 'referral_bonus'")
    )
    total_user_referral_earnings = str(res_ref.scalar() or 0)

    res_admin = await db.execute(
        text(
            "SELECT COALESCE(SUM(amount), 0) FROM transactions "
            "WHERE type = 'referral_bonus' AND user_id = :aid"
        ),
        {"aid": admin["id"]},
    )
    admin_referral_earnings = str(res_admin.scalar() or 0)

    res_wdr = await db.execute(text("SELECT COUNT(*) FROM withdrawals WHERE status = 'pending'"))
    pending_withdrawals_count = res_wdr.scalar() or 0

    res_bal = await db.execute(text("SELECT COALESCE(SUM(balance), 0) FROM users"))
    protocol_balance = str(res_bal.scalar() or 0)

    return AdminStatsResponse(
        total_users=total_users,
        total_user_referral_earnings=total_user_referral_earnings,
        admin_referral_earnings=admin_referral_earnings,
        pending_withdrawals_count=pending_withdrawals_count,
        protocol_balance=protocol_balance,
    )


# -----------------------------
# USERS
# -----------------------------
async def list_users(admin, db: AsyncSession) -> List[AdminUserResponse]:
    query = text("SELECT * FROM users ORDER BY created_at DESC")
    result = await db.execute(query)
    records = result.fetchall()

    return [
        AdminUserResponse(
            id=str(r.id),
            email=r.email,
            username=r.username,
            role=r.role,
            status=r.status,
            withdrawal_status=r.withdrawal_status,
            is_kyc_verified=r.is_kyc_verified,
            balance=str(r.balance),
        )
        for r in records
    ]


async def create_user(admin, payload: AdminUserCreateRequest, db: AsyncSession):
    if admin["role"] != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")

    check_email = await db.execute(
        text("SELECT 1 FROM users WHERE email = :email"), {"email": payload.email}
    )
    if check_email.fetchone():
        raise HTTPException(status_code=400, detail="Email already exists")

    check_username = await db.execute(
        text("SELECT 1 FROM users WHERE username = :uname"), {"uname": payload.username}
    )
    if check_username.fetchone():
        raise HTTPException(status_code=400, detail="Username already exists")

    hashed_pw = hash_password(payload.password)
    referral_code = secrets.token_hex(4).upper()
    referred_by_code = payload.referral_code

    uid = str(uuid4())
    insert_q = text(
        """
        INSERT INTO users (
            id, first_name, last_name, email, username, password_hash,
            referral_code, referred_by_code, role, status, withdrawal_status,
            is_kyc_verified, balance, created_at
        )
        VALUES (
            :id, :fname, :lname, :email, :uname, :pw_hash,
            :referral_code, :referred_by_code, 'user', 'active', 'active',
            false, 0, :dt
        )
    """
    )
    await db.execute(
        insert_q,
        {
            "id": uid,
            "fname": payload.first_name,
            "lname": payload.last_name,
            "email": payload.email,
            "uname": payload.username,
            "pw_hash": hashed_pw,
            "referral_code": referral_code,
            "referred_by_code": referred_by_code,
            "dt": datetime.utcnow(),
        },
    )
    await db.commit()

    return {
        "message": "User created successfully",
        "user_id": uid,
        "referral_code": referral_code,
        "referred_by_code": referred_by_code,
    }


# -----------------------------
# KYC
# -----------------------------
async def list_kyc_requests(admin, db: AsyncSession):
    query = text(
        """
        SELECT
            k.id,
            k.submitted_at AS "dateSubmitted",
            u.username AS "userName",
            u.email AS "userEmail",
            k.address,
            k.city,
            k.postal_code AS "postalCode",
            k.country,
            k.document_front_url AS "documentUrl",
            k.status
        FROM kyc k
        JOIN users u ON u.id = k.user_id
        WHERE k.status = 'pending'
        ORDER BY k.submitted_at DESC
        """
    )
    result = await db.execute(query)
    return result.mappings().all()


async def process_kyc(admin, kyc_id: str, decision: str, rejection_reason: str | None, db: AsyncSession):
    if decision not in ["approved", "rejected"]:
        raise HTTPException(status_code=400, detail="Decision must be 'approved' or 'rejected'")

    if decision == "rejected" and not rejection_reason:
        raise HTTPException(status_code=400, detail="Rejection reason is required when rejecting KYC")

    update_q = text(
        """
        UPDATE kyc
        SET status = :st,
            reviewed_by = :aid,
            reviewed_at = :dt,
            notes = :notes
        WHERE id = :id
        """
    )
    await db.execute(
        update_q,
        {
            "st": decision,
            "aid": admin["id"],
            "dt": datetime.utcnow(),
            "notes": rejection_reason,
            "id": kyc_id,
        },
    )

    if decision == "approved":
        user_update_q = text(
            """
            UPDATE users
            SET is_kyc_verified = true
            WHERE id = (SELECT user_id FROM kyc WHERE id = :id)
            """
        )
        await db.execute(user_update_q, {"id": kyc_id})

    fetch_q = text(
        """
        SELECT
            k.id,
            k.submitted_at AS "dateSubmitted",
            u.username AS "userName",
            u.email AS "userEmail",
            k.address,
            k.city,
            k.postal_code AS "postalCode",
            k.country,
            k.document_front_url AS "documentUrl",
            k.status,
            k.notes,
            k.reviewed_by,
            k.reviewed_at
        FROM kyc k
        JOIN users u ON u.id = k.user_id
        WHERE k.id = :id
        """
    )
    result = await db.execute(fetch_q, {"id": kyc_id})
    record = result.mappings().first()

    await db.commit()
    return record


# -----------------------------
# WITHDRAWALS
# -----------------------------
async def list_withdrawals(admin, db: AsyncSession):
    query = text("SELECT * FROM withdrawals ORDER BY requested_at DESC")
    result = await db.execute(query)
    return [dict(r) for r in result.fetchall()]


async def approve_withdrawal(admin, withdrawal_id: str, db: AsyncSession):
    if admin["role"] != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")

    # Fetch withdrawal
    res = await db.execute(
        text("SELECT * FROM withdrawals WHERE id = :wid AND status = 'pending'"),
        {"wid": withdrawal_id},
    )
    withdrawal = res.mappings().first()
    if not withdrawal:
        raise HTTPException(status_code=404, detail="Withdrawal not found or already processed")

    user_id = withdrawal["user_id"]
    amount = withdrawal["amount"]
    currency = withdrawal["currency"]

    # Deduct from user balance
    await db.execute(
        text("UPDATE users SET balance = balance - :amt WHERE id = :uid"),
        {"amt": amount, "uid": user_id},
    )

    # Mark withdrawal as approved
    await db.execute(
        text("UPDATE withdrawals SET status = 'approved' WHERE id = :wid"),
        {"wid": withdrawal_id},
    )

    # Log transaction
    await db.execute(
        text(
            """
            INSERT INTO transactions (
                id, user_id, type, amount, currency, status, reference, created_at
            ) VALUES (
                :id, :uid, 'withdrawal', :amt, :curr, 'completed', :ref, :dt
            )
            """
        ),
        {
            "id": str(uuid4()),
            "uid": user_id,
            "amt": amount,
            "curr": currency,
            "ref": f"WDR-{withdrawal_id}",
            "dt": datetime.utcnow(),
        },
    )

    await db.commit()
    return {"message": f"Withdrawal {withdrawal_id} approved and transaction logged"}


async def deny_withdrawal(admin, withdrawal_id: str, db: AsyncSession):
    if admin["role"] != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")

    # Fetch withdrawal
    res = await db.execute(
        text("SELECT * FROM withdrawals WHERE id = :wid AND status = 'pending'"),
        {"wid": withdrawal_id},
    )
    withdrawal = res.mappings().first()
    if not withdrawal:
        raise HTTPException(status_code=404, detail="Withdrawal not found or already processed")

    user_id = withdrawal["user_id"]
    amount = withdrawal["amount"]

    # Refund balance if it was already deducted at request time
    await db.execute(
        text("UPDATE users SET balance = balance + :amt WHERE id = :uid"),
        {"amt": amount, "uid": user_id},
    )

    # Mark withdrawal as denied
    await db.execute(
        text("UPDATE withdrawals SET status = 'denied' WHERE id = :wid"),
        {"wid": withdrawal_id},
    )

    await db.commit()
    return {"message": f"Withdrawal {withdrawal_id} denied and balance refunded"}

# -----------------------------
# TRANSACTIONS
# -----------------------------
async def list_transactions(admin, db: AsyncSession):
    query = text("SELECT * FROM transactions ORDER BY created_at DESC")
    result = await db.execute(query)
    return [dict(r) for r in result.fetchall()]

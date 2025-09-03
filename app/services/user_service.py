from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.schemas.user_schemas import (
    ChangePasswordRequest, SetPinRequest, ChangePinRequest, VerifyPinRequest,
    UserUpdateRequest, UserProfileResponse
)
from app.utils.security import (
    hash_password, verify_password,
    hash_pin, verify_pin as verify_pin_util  # 👈 renamed to avoid collision
)


# -----------------------------
# PROFILE
# -----------------------------
async def get_profile(user: dict, db: AsyncSession):
    query = text("""
        SELECT 
            id,
            email,
            username,
            first_name,
            last_name,
            referral_code,
            referred_by_code,
            is_kyc_verified,
            balance,
            role,
            status,
            withdrawal_status,
            is_2fa_enabled,
            withdrawal_pin_hash
        FROM users 
        WHERE id = :id
        LIMIT 1
    """)
    result = await db.execute(query, {"id": user["id"]})
    record = result.fetchone()
    if not record:
        raise HTTPException(status_code=404, detail="User not found")

    return UserProfileResponse(
        id=str(record.id),
        email=record.email,
        username=record.username,
        first_name=record.first_name,
        last_name=record.last_name,
        referral_code=record.referral_code,
        referred_by_code=record.referred_by_code,
        is_kyc_verified=record.is_kyc_verified,
        balance=str(record.balance),
        has_pin=bool(record.withdrawal_pin_hash),  # 👈 derive from DB
        is2fa_enabled=record.is_2fa_enabled,
        role=record.role,
        status=record.status,
        withdrawal_status=record.withdrawal_status,
    )


async def update_profile(user: dict, payload: UserUpdateRequest, db: AsyncSession):
    query = text("""
        UPDATE users 
        SET first_name = :first_name, last_name = :last_name 
        WHERE id = :id
    """)
    await db.execute(query, {"id": user["id"], "first_name": payload.first_name, "last_name": payload.last_name})
    await db.commit()
    return await get_profile(user, db)


# -----------------------------
# PASSWORD
# -----------------------------
async def change_password(user: dict, payload: ChangePasswordRequest, db: AsyncSession):
    query = text("SELECT password_hash FROM users WHERE id = :id")
    result = await db.execute(query, {"id": user["id"]})
    record = result.fetchone()
    if not record:
        raise HTTPException(status_code=404, detail="User not found")

    if not verify_password(payload.old_password, record.password_hash):
        raise HTTPException(status_code=400, detail="Old password is incorrect")

    new_hash = hash_password(payload.new_password)
    update_q = text("UPDATE users SET password_hash = :ph WHERE id = :id")
    await db.execute(update_q, {"id": user["id"], "ph": new_hash})
    await db.commit()
    return {"message": "Password changed successfully"}


# -----------------------------
# PIN
# -----------------------------
async def set_pin(user: dict, payload: SetPinRequest, db: AsyncSession):
    pin_hash = hash_pin(payload.pin)
    query = text("UPDATE users SET withdrawal_pin_hash = :ph, has_pin = true WHERE id = :id")
    await db.execute(query, {"id": user["id"], "ph": pin_hash})
    await db.commit()
    return {"message": "PIN set successfully"}


async def change_pin(user: dict, payload: ChangePinRequest, db: AsyncSession):
    query = text("SELECT password_hash FROM users WHERE id = :id")
    result = await db.execute(query, {"id": user["id"]})
    record = result.fetchone()
    if not record or not verify_password(payload.current_password, record.password_hash):
        raise HTTPException(status_code=400, detail="Invalid current password")

    new_pin_hash = hash_pin(payload.new_pin)
    update_q = text("UPDATE users SET withdrawal_pin_hash = :ph WHERE id = :id")
    await db.execute(update_q, {"id": user["id"], "ph": new_pin_hash})
    await db.commit()
    return {"message": "PIN changed successfully"}


async def verify_user_pin(user: dict, payload: VerifyPinRequest, db: AsyncSession):
    query = text("SELECT withdrawal_pin_hash FROM users WHERE id = :id")
    result = await db.execute(query, {"id": user["id"]})
    record = result.fetchone()
    if not record or not record.withdrawal_pin_hash:
        raise HTTPException(status_code=400, detail="PIN not set")

    if not verify_pin_util(payload.pin, record.withdrawal_pin_hash):
        raise HTTPException(status_code=400, detail="Incorrect PIN")

    return {"message": "PIN verified successfully"}

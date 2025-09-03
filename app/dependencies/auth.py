from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from jose import jwt, JWTError

from app.config import settings
from app.database import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def decode_jwt(token: str):
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )


# -----------------------------
# CURRENT USER
# -----------------------------
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
):
    payload = decode_jwt(token)
    if payload is None or "sub" not in payload:
        raise HTTPException(status_code=401, detail="Invalid authentication")

    # Query DB for user by ID
    query = text("SELECT * FROM users WHERE id = :uid LIMIT 1")
    result = await db.execute(query, {"uid": payload["sub"]})
    user = result.fetchone()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.status != "active":
        raise HTTPException(status_code=403, detail="User account is not active")

    return {
        "id": str(user.id),
        "email": user.email,
        "username": user.username,
        "role": user.role,
        "status": user.status,
        "withdrawal_status": user.withdrawal_status,
    }


# -----------------------------
# CURRENT ADMIN
# -----------------------------
async def get_current_admin(user=Depends(get_current_user)):
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admins only")
    return user

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.services.team_service import get_referral_tree

router = APIRouter(
    prefix="/team",
    tags=["Team"],
)

# -----------------------------
# GET Referral Tree
# -----------------------------
@router.get("/tree/")
async def referral_tree(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get the referral tree for the current authenticated user.
    """
    return await get_referral_tree(current_user["id"], db)  # 🔑 FIXED: use "id"

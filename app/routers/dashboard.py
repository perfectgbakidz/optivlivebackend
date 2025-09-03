# app/routers/dashboard.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.dashboard_schemas import UserDashboardStatsResponse
from app.services import dashboard_service
from app.dependencies import get_current_user
from app.database import get_db

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/stats/", response_model=UserDashboardStatsResponse)
async def get_dashboard_stats(
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await dashboard_service.get_user_dashboard_stats(user, db)

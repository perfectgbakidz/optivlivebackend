# app/services/dashboard_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.schemas.dashboard_schemas import UserDashboardStatsResponse


async def get_user_dashboard_stats(user: dict, db: AsyncSession) -> UserDashboardStatsResponse:
    """
    Return dashboard statistics for a specific user.
    """

    # Total earnings (sum of user’s transactions)
    res_earn = await db.execute(
        text("SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE user_id = :uid"),
        {"uid": user["id"]}
    )
    total_earnings = float(res_earn.scalar() or 0)

    # Direct referrals
    res_direct = await db.execute(
        text("""
            SELECT COUNT(*) 
            FROM users 
            WHERE referred_by_code = (SELECT referral_code FROM users WHERE id = :uid)
        """),
        {"uid": user["id"]}
    )
    direct_referrals = res_direct.scalar() or 0

    # Team size (currently only direct referrals, can be recursive if needed)
    total_team_size = direct_referrals

    return UserDashboardStatsResponse(
        totalEarnings=total_earnings,
        totalTeamSize=total_team_size,
        directReferrals=direct_referrals
    )

from pydantic import BaseModel

class UserDashboardStatsResponse(BaseModel):
    totalEarnings: float
    totalTeamSize: int
    directReferrals: int

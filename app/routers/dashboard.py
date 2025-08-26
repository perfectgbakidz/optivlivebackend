from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from .. import models, database, auth

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


# --------------------------
# Get Dashboard Stats
# --------------------------
@router.get("/stats/")
def get_dashboard_stats(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """
    Returns dashboard stats for the logged-in user.
    Shape must match frontend expectations.
    """

    # ✅ Total earnings = sum of completed referral_bonus + commission transactions
    total_earnings = (
        db.query(models.Transaction)
        .filter(
            models.Transaction.user_id == current_user.id,
            models.Transaction.type.in_(["referral_bonus", "commission"]),
            models.Transaction.status == "completed"
        )
        .with_entities(models.Transaction.amount)
        .all()
    )
    total_earnings_value = sum(float(t.amount) for t in total_earnings)

    # ✅ Direct referrals = count of users referred by this user
    direct_referrals = (
        db.query(models.User)
        .filter(models.User.parent_referral == current_user.referral_code)
        .count()
    )

    # ✅ Total team size = recursive calculation (all downlines)
    def get_team_size(user_ref_code: str) -> int:
        children = (
            db.query(models.User)
            .filter(models.User.parent_referral == user_ref_code)
            .all()
        )
        size = len(children)
        for child in children:
            size += get_team_size(child.referral_code)
        return size

    total_team_size = get_team_size(current_user.referral_code)

    return {
        "totalEarnings": total_earnings_value,
        "totalTeamSize": total_team_size,
        "directReferrals": direct_referrals,
    }

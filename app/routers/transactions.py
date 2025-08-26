from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from .. import models, schemas, database, auth

router = APIRouter(prefix="/transactions", tags=["Transactions"])


# --------------------------
# Get all user transactions
# --------------------------
@router.get("/", response_model=List[schemas.TransactionResponse])
def get_transactions(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user),
    status: Optional[str] = Query(None, description="Filter by status: pending | completed | failed"),
    tx_type: Optional[str] = Query(None, description="Filter by transaction type: withdrawal | deposit | referral_bonus")
):
    """
    Returns all transactions for the logged-in user.
    Supports optional filtering by status and tx_type.
    """

    query = db.query(models.Transaction).filter(models.Transaction.user_id == current_user.id)

    if status:
        query = query.filter(models.Transaction.status == status)
    if tx_type:
        query = query.filter(models.Transaction.tx_type == tx_type)

    transactions = query.order_by(models.Transaction.created_at.desc()).all()
    return transactions

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.schemas.transaction_schemas import TransactionResponse
from app.services import transaction_service
from app.dependencies import get_current_user
from app.database import get_db

router = APIRouter(prefix="/transactions", tags=["Transactions"])


@router.get("/", response_model=List[TransactionResponse])
async def list_transactions(
    user=Depends(get_current_user),
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
):
    return await transaction_service.list_transactions(user, page, page_size, db)


@router.get("/{transaction_id}/", response_model=TransactionResponse)
async def get_transaction(
    transaction_id: str,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await transaction_service.get_transaction(user, transaction_id, db)

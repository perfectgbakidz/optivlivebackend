from fastapi import APIRouter, Depends
from app.schemas.withdrawal_schemas import WithdrawalCreateRequest, WithdrawalResponse
from app.services import withdrawal_service
from app.dependencies import get_current_user
from typing import List

router = APIRouter(prefix="/withdrawals", tags=["Withdrawals"])


@router.get("/", response_model=List[WithdrawalResponse])
async def list_withdrawals(user=Depends(get_current_user)):
    return await withdrawal_service.list_withdrawals(user)


@router.post("/", response_model=WithdrawalResponse)
async def create_withdrawal(payload: WithdrawalCreateRequest, user=Depends(get_current_user)):
    return await withdrawal_service.create_withdrawal(user, payload)

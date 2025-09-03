from fastapi import APIRouter
from app.services import public_service

router = APIRouter(prefix="/public", tags=["Public"])


@router.post("/contact/")
async def contact_form(payload: dict):
    return await public_service.contact_form(payload)

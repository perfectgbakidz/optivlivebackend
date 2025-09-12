# app/routers/webhook_router.py
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.services import webhook_service
from app.config import settings
import logging

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])
logger = logging.getLogger(__name__)


@router.post("/stripe/")
async def stripe_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Stripe webhook handler.
    Triggered after a payment is successfully processed.
    Responsible for creating the final user account from
    pending_registrations.
    """

    # In production → verify Stripe signature strictly
    # In development → allow bypass if DEBUG=True
    if settings.DEBUG:
        logger.warning("⚠️ DEBUG mode: skipping Stripe signature verification")
        return await webhook_service.handle_stripe_webhook(request, db)
    else:
        return await webhook_service.handle_stripe_webhook(request, db)

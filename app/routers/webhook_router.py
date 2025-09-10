from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.services import webhook_service

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


@router.post("/stripe/")
async def stripe_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Stripe webhook handler.
    Triggered after a payment is successfully processed.
    Responsible for creating the final user account from
    pending_registrations.
    """
    sig_header = request.headers.get("stripe-signature")
    if not sig_header:
        raise HTTPException(status_code=400, detail="Missing Stripe signature")

    return await webhook_service.handle_stripe_webhook(request, db)

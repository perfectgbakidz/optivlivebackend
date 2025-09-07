import stripe
from fastapi import HTTPException
from app.config import settings

# Configure Stripe with your secret key
stripe.api_key = settings.STRIPE_SECRET_KEY


# -----------------------------
# Payment Intent Creation
# -----------------------------
def create_payment_intent(amount: int, currency: str, metadata: dict):
    try:
        payment_intent = stripe.PaymentIntent.create(
            amount=amount,
            currency=currency,
            metadata=metadata
        )
        return payment_intent
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stripe error: {str(e)}")


# -----------------------------
# Payout Creation
# -----------------------------
def create_payout(amount: int, currency: str, destination: str):
    """
    Creates a Stripe Payout to a connected account or bank.
    - amount: integer in smallest currency unit (e.g., cents)
    - currency: "usd", "gbp", etc.
    - destination: connected account ID or external account ID
    """
    try:
        payout = stripe.Payout.create(
            amount=amount,
            currency=currency,
            destination=destination
        )
        return payout
    except stripe.error.StripeError as e:  # type: ignore
        raise HTTPException(status_code=500, detail=f"Stripe payout error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected payout error: {str(e)}")


# -----------------------------
# Webhook Event Verification
# -----------------------------
def verify_webhook_signature(payload: bytes, sig_header: str):
    """
    Verifies the webhook signature to ensure authenticity.
    """
    try:
        event = stripe.Webhook.construct_event(
            payload=payload,
            sig_header=sig_header,
            secret=settings.STRIPE_WEBHOOK_SECRET
        )
        return event
    except stripe.error.SignatureVerificationError:  # type: ignore
        raise HTTPException(status_code=400, detail="Invalid Stripe signature")
    except stripe.error.StripeError as e:  # type: ignore
        raise HTTPException(status_code=400, detail=f"Stripe error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Webhook verification failed: {str(e)}")

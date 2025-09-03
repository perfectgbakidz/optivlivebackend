import stripe
import os

stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "sk_test_dummy")


def create_payment_intent(amount: int, currency: str = "usd", metadata: dict = None):
    """
    Create a Stripe PaymentIntent for deposits
    """
    return stripe.PaymentIntent.create(
        amount=amount,
        currency=currency,
        metadata=metadata or {},
    )


def create_payout(amount: int, currency: str = "usd", destination: str = None):
    """
    Create a Stripe Payout for withdrawals
    """
    return stripe.Payout.create(
        amount=amount,
        currency=currency,
        destination=destination,
    )

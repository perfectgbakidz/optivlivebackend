import random
import string

# -----------------------------
# REFERRAL + TRANSACTION HELPERS
# -----------------------------

def generate_referral_code(length: int = 8) -> str:
    """Generate a random alphanumeric referral code."""
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=length))


def generate_transaction_ref(prefix: str = "TX") -> str:
    """Generate a transaction reference with a given prefix."""
    return f"{prefix}-{''.join(random.choices(string.ascii_uppercase + string.digits, k=10))}"


# -----------------------------
# REFERRAL BONUS HELPERS
# -----------------------------

MASTER_REFERRAL_CODE = "MASTERKEY"

# Tier reductions (relative to Tier 1)
REFERRAL_REDUCTION_FACTORS = [1.0, 0.85, 0.70, 0.55, 0.40, 0.25]


def calculate_tier_bonus(signup_fee: float, tier: int, base_percentage: float = 0.20) -> float:
    """
    Calculate the bonus for a given referral tier.
    - signup_fee: Total fee paid (e.g., 50.0)
    - tier: 1 through 6
    - base_percentage: Default 20% of signup fee is Tier 1 bonus
    """
    if tier < 1 or tier > 6:
        raise ValueError("Tier must be between 1 and 6")

    tier1_bonus = signup_fee * base_percentage
    reduction = REFERRAL_REDUCTION_FACTORS[tier - 1]
    return round(tier1_bonus * reduction, 2)

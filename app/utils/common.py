import random
import string


def generate_referral_code(length: int = 8) -> str:
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=length))


def generate_transaction_ref(prefix: str = "TX") -> str:
    return f"{prefix}-{''.join(random.choices(string.ascii_uppercase + string.digits, k=10))}"

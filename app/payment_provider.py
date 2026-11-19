import hashlib
import hmac
import secrets

from app.security import SECRET_KEY


def _sign(provider_order_id: str, provider_payment_id: str) -> str:
    message = f"{provider_order_id}|{provider_payment_id}".encode()
    return hmac.new(SECRET_KEY.encode(), message, hashlib.sha256).hexdigest()


def create_provider_order(amount: float) -> str:
    return "order_fake_" + secrets.token_hex(8)


def simulate_checkout(provider_order_id: str) -> tuple[str, str]:
    provider_payment_id = "pay_fake_" + secrets.token_hex(8)
    return provider_payment_id, _sign(provider_order_id, provider_payment_id)


def verify_signature(
    provider_order_id: str, provider_payment_id: str, signature: str
) -> bool:
    expected = _sign(provider_order_id, provider_payment_id)
    return hmac.compare_digest(expected, signature)
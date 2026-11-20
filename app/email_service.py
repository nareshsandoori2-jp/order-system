import logging

logger = logging.getLogger("uvicorn.error")


def send_order_confirmation(to_email: str, order_id: int, total: float) -> None:
    """Simulated email sender. Replace the body with a real email API later."""
    logger.info(
        "EMAIL to %s: your order #%s (total %.2f) was placed",
        to_email,
        order_id,
        total,
    )
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import payment_provider
from app.database import get_db
from app.deps import get_current_user
from app.models import Order, Payment, User
from app.schemas import PaymentCreate, PaymentOut, PaymentVerify, SimulatedCheckout

router = APIRouter(prefix="/payments", tags=["payments"])


@router.post("", response_model=PaymentOut, status_code=201)
def create_payment(
    data: PaymentCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    order = db.get(Order, data.order_id, with_for_update=True)
    if order is None or order.user_id != user.id:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.status != "placed":
        raise HTTPException(status_code=400, detail="Order is not payable")

    # Idempotent: reuse an unpaid payment instead of creating a second one
    existing = db.scalar(
        select(Payment).where(
            Payment.order_id == order.id, Payment.status == "created"
        )
    )
    if existing:
        return existing

    payment = Payment(
        order_id=order.id,
        amount=order.total,
        provider_order_id=payment_provider.create_provider_order(order.total),
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return payment


@router.post("/{payment_id}/simulate-checkout", response_model=SimulatedCheckout)
def simulate_checkout(
    payment_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Stands in for the Razorpay checkout page. Demo only."""
    payment = db.get(Payment, payment_id)
    if payment is None:
        raise HTTPException(status_code=404, detail="Payment not found")
    order = db.get(Order, payment.order_id)
    if order.user_id != user.id:
        raise HTTPException(status_code=404, detail="Payment not found")
    if payment.status != "created":
        raise HTTPException(status_code=400, detail="Payment is not pending")

    provider_payment_id, signature = payment_provider.simulate_checkout(
        payment.provider_order_id
    )
    return SimulatedCheckout(
        provider_order_id=payment.provider_order_id,
        provider_payment_id=provider_payment_id,
        signature=signature,
    )


@router.post("/verify", response_model=PaymentOut)
def verify_payment(
    data: PaymentVerify,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    payment = db.scalar(
        select(Payment)
        .where(Payment.provider_order_id == data.provider_order_id)
        .with_for_update()
    )
    if payment is None:
        raise HTTPException(status_code=404, detail="Payment not found")
    order = db.get(Order, payment.order_id, with_for_update=True)
    if order.user_id != user.id:
        raise HTTPException(status_code=404, detail="Payment not found")

    if payment.status == "paid":
        return payment  # already verified, calling again is safe

    if not payment_provider.verify_signature(
        data.provider_order_id, data.provider_payment_id, data.signature
    ):
        raise HTTPException(status_code=400, detail="Invalid payment signature")
    if order.status != "placed":
        raise HTTPException(status_code=400, detail="Order is not payable")

    payment.status = "paid"
    payment.provider_payment_id = data.provider_payment_id
    order.status = "paid"
    db.commit()
    db.refresh(payment)
    return payment
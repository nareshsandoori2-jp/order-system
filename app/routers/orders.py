from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.database import get_db
from app.deps import get_current_user, require_admin
from app.models import Order, OrderItem, Product, User
from app.schemas import OrderCreate, OrderOut, StatusUpdate

router = APIRouter(prefix="/orders", tags=["orders"])

ALLOWED_NEXT = {"placed": "paid", "paid": "shipped", "shipped": "delivered"}


@router.post("", response_model=OrderOut, status_code=201)
def create_order(
    data: OrderCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    # Merge duplicate products into one quantity
    quantities: dict[int, int] = defaultdict(int)
    for item in data.items:
        quantities[item.product_id] += item.quantity

    # Lock the product rows so two buyers can't take the last item together
    products = db.scalars(
        select(Product)
        .where(Product.id.in_(quantities.keys()))
        .order_by(Product.id)
        .with_for_update()
    ).all()
    found = {p.id: p for p in products}

    missing = set(quantities) - set(found)
    if missing:
        raise HTTPException(status_code=404, detail=f"Products not found: {sorted(missing)}")

    order = Order(user_id=user.id)
    total = 0.0
    for product_id, qty in quantities.items():
        product = found[product_id]
        if product.stock < qty:
            raise HTTPException(
                status_code=400, detail=f"Not enough stock for {product.name}"
            )
        product.stock -= qty
        total += product.price * qty
        order.items.append(
            OrderItem(product_id=product_id, quantity=qty, price=product.price)
        )

    order.total = total
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


@router.get("", response_model=list[OrderOut])
def list_my_orders(
    db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    stmt = (
        select(Order)
        .where(Order.user_id == user.id)
        .options(selectinload(Order.items))
        .order_by(Order.id.desc())
    )
    return db.scalars(stmt).all()


@router.get("/{order_id}", response_model=OrderOut)
def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    order = db.get(Order, order_id)
    if order is None or (order.user_id != user.id and user.role != "admin"):
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@router.patch("/{order_id}/cancel", response_model=OrderOut)
def cancel_order(
    order_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    order = db.get(Order, order_id)
    if order is None or (order.user_id != user.id and user.role != "admin"):
        raise HTTPException(status_code=404, detail="Order not found")
    if order.status != "placed":
        raise HTTPException(
            status_code=400, detail="Only orders with status 'placed' can be cancelled"
        )
    for item in order.items:
        product = db.get(Product, item.product_id, with_for_update=True)
        product.stock += item.quantity
    order.status = "cancelled"
    db.commit()
    db.refresh(order)
    return order


@router.patch("/{order_id}/status", response_model=OrderOut)
def update_status(
    order_id: int,
    data: StatusUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    order = db.get(Order, order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    if ALLOWED_NEXT.get(order.status) != data.status:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot change status from '{order.status}' to '{data.status}'",
        )
    order.status = data.status
    db.commit()
    db.refresh(order)
    return order
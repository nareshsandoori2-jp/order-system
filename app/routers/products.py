from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Product as ProductModel
from app.schemas import Product, ProductCreate

router = APIRouter(prefix="/products", tags=["products"])


@router.post("", response_model=Product, status_code=201)
def create_product(data: ProductCreate, db: Session = Depends(get_db)):
    product = ProductModel(**data.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@router.get("", response_model=list[Product])
def list_products(db: Session = Depends(get_db)):
    return db.scalars(select(ProductModel).order_by(ProductModel.id)).all()


@router.get("/{product_id}", response_model=Product)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.get(ProductModel, product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.put("/{product_id}", response_model=Product)
def update_product(product_id: int, data: ProductCreate, db: Session = Depends(get_db)):
    product = db.get(ProductModel, product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    for field, value in data.model_dump().items():
        setattr(product, field, value)
    db.commit()
    db.refresh(product)
    return product


@router.delete("/{product_id}", status_code=204)
def delete_product(product_id: int, db: Session = Depends(get_db)):
    product = db.get(ProductModel, product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    db.delete(product)
    db.commit()
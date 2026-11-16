from fastapi import APIRouter, HTTPException
from app.schemas import Product, ProductCreate

router = APIRouter(prefix="/products", tags=["products"])

products_db: dict[int, Product] = {}
next_id = 1


@router.post("", response_model=Product, status_code=201)
def create_product(data: ProductCreate):
    global next_id
    product = Product(id=next_id, **data.model_dump())
    products_db[next_id] = product
    next_id += 1
    return product


@router.get("", response_model=list[Product])
def list_products():
    return list(products_db.values())


@router.get("/{product_id}", response_model=Product)
def get_product(product_id: int):
    if product_id not in products_db:
        raise HTTPException(status_code=404, detail="Product not found")
    return products_db[product_id]


@router.put("/{product_id}", response_model=Product)
def update_product(product_id: int, data: ProductCreate):
    if product_id not in products_db:
        raise HTTPException(status_code=404, detail="Product not found")
    product = Product(id=product_id, **data.model_dump())
    products_db[product_id] = product
    return product


@router.delete("/{product_id}", status_code=204)
def delete_product(product_id: int):
    if product_id not in products_db:
        raise HTTPException(status_code=404, detail="Product not found")
    del products_db[product_id]
from fastapi import FastAPI

from app.routers import auth, orders, payments, products

app = FastAPI(title="Order System")

app.include_router(auth.router)
app.include_router(products.router)
app.include_router(orders.router)
app.include_router(payments.router)


@app.get("/health")
def health():
    return {"status": "ok"}
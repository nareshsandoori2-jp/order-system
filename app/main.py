from fastapi import FastAPI

from app.routers import auth, orders, products

app = FastAPI(title="Order System")

app.include_router(auth.router)
app.include_router(products.router)
app.include_router(orders.router)


@app.get("/health")
def health():
    return {"status": "ok"}
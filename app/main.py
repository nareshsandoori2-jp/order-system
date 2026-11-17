from fastapi import FastAPI
from app.database import Base, engine
from app import models
from app.routers import auth, orders, products

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Order System")

app.include_router(auth.router)
app.include_router(products.router)
app.include_router(orders.router)


@app.get("/health")
def health():
    return {"status": "ok"}
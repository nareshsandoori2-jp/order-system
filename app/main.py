from fastapi import FastAPI
from app.database import Base, engine
from app import models
from app.routers import auth, products

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Order System")

app.include_router(auth.router)
app.include_router(products.router)


@app.get("/health")
def health():
    return {"status": "ok"}
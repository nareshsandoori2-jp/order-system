from pydantic import BaseModel, ConfigDict, Field


class ProductCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    price: float = Field(gt=0)
    stock: int = Field(ge=0)


class Product(ProductCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
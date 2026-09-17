from pydantic import BaseModel
from app.models.product import Unit


class ProductCreate(BaseModel):
    name: str
    category_id: int
    price: float
    quantity: float
    unit: Unit
    description: str | None = None


class ProductUpdate(BaseModel):
    name: str | None = None
    category_id: int | None = None
    price: float | None = None
    quantity: float | None = None
    unit: Unit | None = None
    description: str | None = None


class ProductCategoryOut(BaseModel):
    id: int
    name: str
    image_url: str

    class Config:
        from_attributes = True


# краткая публичная информация о поставщике, вложенная в ответ о товаре
class ProductSupplierOut(BaseModel):
    id: int
    name: str
    description: str | None
    contact_phone: str | None

    class Config:
        from_attributes = True


class ProductOut(BaseModel):
    id: int
    name: str
    category: ProductCategoryOut
    supplier: ProductSupplierOut
    price: float
    quantity: float
    unit: Unit
    description: str | None

    class Config:
        from_attributes = True
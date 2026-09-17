from datetime import datetime
from pydantic import BaseModel
from app.models.order import SubOrderStatus


class OrderItemCreate(BaseModel):
    product_id: int
    quantity: float


class OrderCreate(BaseModel):
    items: list[OrderItemCreate]


# краткая информация о товаре, вложенная в позицию заказа
class OrderItemProductOut(BaseModel):
    id: int
    name: str
    unit: str

    class Config:
        from_attributes = True


class OrderItemOut(BaseModel):
    id: int
    product: OrderItemProductOut
    quantity: float
    price_at_purchase: float

    class Config:
        from_attributes = True


class SubOrderSupplierOut(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class SubOrderOut(BaseModel):
    id: int
    supplier: SubOrderSupplierOut
    amount: float
    status: SubOrderStatus
    created_at: datetime
    items: list[OrderItemOut]

    class Config:
        from_attributes = True


class OrderOut(BaseModel):
    id: int
    sub_orders: list[SubOrderOut]

    class Config:
        from_attributes = True


class SubOrderStatusUpdate(BaseModel):
    status: SubOrderStatus
from pydantic import BaseModel
from app.models.payment import PaymentMethod, PaymentStatus
from app.models.payment import TransactionType



# что клиент присылает, чтобы оплатить под-заказ
class PaymentCreate(BaseModel):
    method: PaymentMethod

# что мы отдаём в ответ после оплаты
class PaymentOut(BaseModel):
    id: int
    sub_order_id: int
    amount: float
    method: PaymentMethod
    status: PaymentStatus

    class Config:
        from_attributes = True

class SupplierTransactionOut(BaseModel):
    id: int
    sub_order_id: int
    amount: float
    type: TransactionType
    balance_after: float

    class Config:
        from_attributes = True


class SupplierFinanceOut(BaseModel):
    balance: float
    transactions: list[SupplierTransactionOut]
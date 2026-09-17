import enum
from sqlalchemy import Column, Integer,String, Numeric, Enum, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base

class PaymentMethod(str, enum.Enum):
    card = "card"  # оплата картой
    qr = "qr"  # оплата через QR

class PaymentStatus(str, enum.Enum):
    pending = "pending"  # платёж создан, ожидает результата
    success = "success"  # успешно оплачено
    failed = "failed"  # не удалось оплатить

class TransactionType(str, enum.Enum):
    sale = "sale"  # начисление за продажу
    withdrawal = "withdrawal"  # вывод средств (на будущее)

class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    sub_order_id = Column(Integer, ForeignKey("sub_orders.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    method = Column(Enum(PaymentMethod), nullable=False)
    status = Column(Enum(PaymentStatus), default=PaymentStatus.pending, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    sub_order = relationship("SubOrder")
    user = relationship("User")

class SupplierTransaction(Base):
    __tablename__ = "supplier_transactions"

    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False)
    sub_order_id = Column(Integer, ForeignKey("sub_orders.id"), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    type = Column(Enum(TransactionType), nullable=False)
    balance_after = Column(Numeric(12, 2), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    supplier = relationship("Supplier")
    sub_order = relationship("SubOrder")

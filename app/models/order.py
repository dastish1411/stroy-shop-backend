import enum
from sqlalchemy import Column, Integer, String, Numeric, Enum, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base

class SubOrderStatus(str, enum.Enum):
    pending_payment = "pending_payment"
    paid = "paid"
    processing = "processing"
    shipped = "shipped"
    delivered = "delivered"
    cancelled = "cancelled"

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User")
    # sub_orders - список всех под-заказов этого общего заказа
    # back_populates связывает это поле с полем "order" в модели SubOrder ниже,
    # чтобы можно было ходить в обе стороны: order.sub_orders и sub_order.order
    sub_orders = relationship("SubOrder", back_populates="order")

class SubOrder(Base):
    __tablename__ = "sub_orders"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    status = Column(Enum(SubOrderStatus), default=SubOrderStatus.pending_payment, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    order = relationship("Order", back_populates="sub_orders")
    supplier = relationship("Supplier")
    items = relationship("OrderItem", back_populates="sub_order")

class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    sub_order_id = Column(Integer, ForeignKey("sub_orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Numeric(12, 3), nullable=False)
    price_at_purchase = Column(Numeric(12, 2), nullable=False)

    sub_order = relationship("SubOrder", back_populates="items")
    product = relationship("Product")
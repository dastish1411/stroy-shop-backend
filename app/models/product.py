import enum
from sqlalchemy import Column, Integer, String, Numeric, Enum, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base

class Unit(str, enum.Enum):
    kg = "kg"
    piece = "piece"

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False)
    price = Column(Numeric(12, 2), nullable=False)
    quantity = Column(Numeric(12, 3), nullable=False, default=0)
    unit = Column(Enum(Unit), nullable=False)
    description = Column(String,nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    category = relationship("Category")
    supplier = relationship("Supplier")

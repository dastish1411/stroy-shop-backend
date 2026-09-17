from sqlalchemy import Column, Integer, String, Numeric, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base

class Supplier(Base):
    __tablename__ = "suppliers"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    contact_phone = Column(String, nullable=True)
    balance = Column(Numeric(12, 2), default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # relationship - это НЕ настоящая колонка в базе, а удобная "ссылка" в Python-коде,
    # которая позволяет писать supplier.owner и сразу получать связанного пользователя,
    # вместо того чтобы делать отдельный запрос в базу
    owner = relationship("User")
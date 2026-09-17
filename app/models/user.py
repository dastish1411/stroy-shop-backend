import enum
from sqlalchemy import Column, Integer, String, Enum, DateTime
from sqlalchemy.sql import func
from app.db.base import Base

# enum - это ограниченный набор допустимых значений для роли пользователя
# нельзя будет записать в базу что-то, кроме этих трёх вариантов
class UserRole(str, enum.Enum):
    client = "client"
    supplier = "supplier"
    admin = "admin"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    role = Column(Enum(UserRole), default=UserRole.client, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

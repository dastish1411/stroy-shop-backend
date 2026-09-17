from pydantic import BaseModel, EmailStr
from app.models.user import UserRole

# Схема для РЕГИСТРАЦИИ - что клиент присылает нам
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str | None = None
    phone: str | None = None
    role: UserRole = UserRole.client
    company_name: str | None = None  # обязательно, только если role = supplier

# Схема для ЛОГИНА - что клиент присылает при входе
class UserLogin(BaseModel):
    email: EmailStr
    password: str


# Схема для ОТВЕТА - что МЫ отдаём клиенту (без пароля!)
class UserOut(BaseModel):
    id: int
    email: EmailStr
    full_name: str | None
    phone: str | None
    role: UserRole

    class Config:
        # позволяет Pydantic читать данные напрямую из SQLAlchemy-объекта
        # (а не только из словаря), это нужно, чтобы отдавать модель User как есть
        from_attributes = True


# Схема ответа при логине - отдаём токен
class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


# Схема для запроса обновления access token
class RefreshRequest(BaseModel):
    refresh_token: str
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.core.config import settings
from app.models.user import User, UserRole
from app.models.supplier import Supplier


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# HTTPBearer - простая схема: Swagger просто попросит вставить сам токен,
# без формы логина, как это было с OAuth2PasswordBearer
bearer_scheme = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=401,
        detail="Не удалось подтвердить личность пользователя",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token = credentials.credentials  # сам токен, без слова "Bearer"

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception

    return user

def get_current_supplier(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
) -> Supplier:
    if current_user.role != UserRole.supplier:
        raise HTTPException(status_code=403, detail="Доступно только для поставщиков")

    supplier = db.query(Supplier).filter(Supplier.owner_id ==  current_user.id).first()
    if not supplier:
        raise HTTPException(
            status_code=404,
            detail="Профиль поставщика не найден. Сначала создайте профиль компании",
        )
    return supplier

def get_current_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Доступно только для администратора")
    return current_user
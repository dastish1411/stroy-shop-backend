from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
from jose import jwt
from app.core.config import settings
import secrets

# CryptContext - инструмент для хэширования паролей.
# Мы никогда не храним пароль в открытом виде в базе - только его хэш
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    # превращает обычный пароль в хэш (необратимую "зашифрованную" строку)
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    # сравнивает введённый пароль с хэшем из базы
    # (сам хэш расшифровать нельзя, но можно проверить, что пароль ему соответствует)
    return  pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict) -> str:
    # создаёт JWT-токен, который будет подтверждать личность пользователя
    # без необходимости каждый раз запрашивать логин/пароль
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def create_refresh_token() -> str:
    # secrets.token_urlsafe - генерирует случайную, криптографически надёжную строку
    # это НЕ JWT, просто длинная случайная строка - этого достаточно,
    # т.к. мы будем хранить и проверять её через базу данных, а не через подпись
    return secrets.token_urlsafe(32)


def get_refresh_token_expiry() -> datetime:
    # refresh token живёт намного дольше access token - например, 30 дней
    return datetime.now(timezone.utc) + timedelta(days=30)
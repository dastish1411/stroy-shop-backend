from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.schemas.user import UserCreate, UserLogin, UserOut, Token, RefreshRequest
from app.crud.user import get_user_by_email, create_user
from app.crud.refresh_token import (
    create_user_refresh_token,
    get_valid_refresh_token,
    revoke_refresh_token,
)
from app.core.security import verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    existing_user = get_user_by_email(db, user_data.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Пользователь с таким email уже существует")

    new_user = create_user(db, user_data)
    return new_user


@router.post("/login", response_model=Token)
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    user = get_user_by_email(db, credentials.email)

    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Неверный email или пароль")

    access_token = create_access_token(data={"sub": user.email})
    refresh_token = create_user_refresh_token(db, user)

    return Token(access_token=access_token, refresh_token=refresh_token.token)


@router.post("/refresh", response_model=Token)
def refresh(request: RefreshRequest, db: Session = Depends(get_db)):
    token_record = get_valid_refresh_token(db, request.refresh_token)

    if not token_record:
        raise HTTPException(status_code=401, detail="Недействительный refresh token")

    # проверяем срок действия отдельно, чтобы дать понятное сообщение
    if token_record.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Срок действия refresh token истёк, войдите заново")

    # выдаём новый access token
    new_access_token = create_access_token(data={"sub": token_record.user.email})

    # отзываем старый refresh token и выдаём новый (это называется "ротация" токенов -
    # повышает безопасность, старый токен больше нельзя использовать повторно)
    revoke_refresh_token(db, token_record)
    new_refresh_token = create_user_refresh_token(db, token_record.user)

    return Token(access_token=new_access_token, refresh_token=new_refresh_token.token)


@router.post("/logout")
def logout(request: RefreshRequest, db: Session = Depends(get_db)):
    token_record = get_valid_refresh_token(db, request.refresh_token)

    if token_record:
        revoke_refresh_token(db, token_record)

    return {"message": "Вы вышли из системы"}

@router.get("/me", response_model=UserOut)
def get_me(current_user=Depends(get_current_user)):
    # просто возвращаем данные текущего пользователя,
    # чтобы проверить, что токен реально распознаётся
    return current_user
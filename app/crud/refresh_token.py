from sqlalchemy.orm import Session
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.core.security import create_refresh_token, get_refresh_token_expiry


def create_user_refresh_token(db: Session, user: User) -> RefreshToken:
    # создаём новую случайную строку токена
    token_str = create_refresh_token()

    refresh_token = RefreshToken(
        user_id=user.id,
        token=token_str,
        expires_at=get_refresh_token_expiry(),
    )
    db.add(refresh_token)
    db.commit()
    db.refresh(refresh_token)
    return refresh_token


def get_valid_refresh_token(db: Session, token_str: str) -> RefreshToken | None:
    # ищем токен по строке, который ещё НЕ отозван
    return db.query(RefreshToken).filter(
        RefreshToken.token == token_str,
        RefreshToken.revoked == False,
    ).first()


def revoke_refresh_token(db: Session, refresh_token: RefreshToken) -> None:
    # помечаем токен как отозванный (используется для logout)
    refresh_token.revoked = True
    db.commit()
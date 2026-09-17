from sqlalchemy.orm import Session
from app.models.user import User, UserRole
from app.models.supplier import Supplier
from app.schemas.user import UserCreate
from app.core.security import hash_password


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email).first()


def create_user(db: Session, user_data: UserCreate) -> User:
    new_user = User(
        email=user_data.email,
        hashed_password=hash_password(user_data.password),
        full_name=user_data.full_name,
        phone=user_data.phone,
        role=user_data.role,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # если регистрируется поставщик - сразу создаём его профиль компании
    if new_user.role == UserRole.supplier:
        supplier = Supplier(
            owner_id=new_user.id,
            name=user_data.company_name or f"Поставщик {new_user.email}",
        )
        db.add(supplier)
        db.commit()

    return new_user
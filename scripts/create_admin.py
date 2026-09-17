"""
Скрипт для создания администратора.
Запускать вручную на сервере: python3 scripts/create_admin.py
Внутри Docker: docker compose exec backend python3 scripts/create_admin.py
"""
import sys
import os

sys.path.append(os.getcwd())

from app.db.session import SessionLocal
from app.models.user import User, UserRole
from app.core.security import hash_password


def main():
    db = SessionLocal()

    email = input("Email администратора: ").strip()
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        print(f"Ошибка: пользователь с email {email} уже существует")
        return

    password = input("Пароль: ").strip()
    full_name = input("Имя (необязательно): ").strip() or None

    admin = User(
        email=email,
        hashed_password=hash_password(password),
        full_name=full_name,
        role=UserRole.admin,
    )
    db.add(admin)
    db.commit()

    print(f"Администратор {email} успешно создан")


if __name__ == "__main__":
    main()

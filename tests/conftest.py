import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.base import Base
from app.api.deps import get_db
from app.models.user import User, UserRole
from app.core.security import hash_password

SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture()
def client():
    Base.metadata.create_all(bind=engine)
    yield TestClient(app)
    Base.metadata.drop_all(bind=engine)


def create_admin_directly(email="admin@example.com", password="test123"):
    # создаёт админа НАПРЯМУЮ в базе, в обход защищённого /auth/register -
    # именно так это работает и в реальности через scripts/create_admin.py
    db = TestingSessionLocal()
    admin = User(
        email=email,
        hashed_password=hash_password(password),
        role=UserRole.admin,
    )
    db.add(admin)
    db.commit()
    db.close()
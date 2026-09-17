from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# engine - это "движок", который знает, как физически подключаться к базе данных
engine = create_engine(settings.DATABASE_URL)

# SessionLocal - фабрика сессий. Каждая сессия - это одно "общение" с базой
# (открыли, сделали запросы, закрыли)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
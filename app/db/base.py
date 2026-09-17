from sqlalchemy.orm import declarative_base

# Base - это родительский класс, от которого будут наследоваться
# ВСЕ наши модели (User, Product, Order и т.д.)
# Благодаря этому SQLAlchemy понимает, какие классы нужно превращать в таблицы
Base = declarative_base()
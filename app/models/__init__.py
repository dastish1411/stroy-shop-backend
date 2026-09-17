# Этот файл нужен для того, чтобы при импорте "app.models"
# Python сразу подтягивал ВСЕ модели разом.
# Alembic (миграции) будет смотреть именно сюда, чтобы понять,
# какие таблицы нужно создать в базе данных.

from app.models.user import User
from app.models.supplier import Supplier
from app.models.category import Category
from app.models.product import Product
from app.models.order import Order, SubOrder, OrderItem
from app.models.payment import Payment, SupplierTransaction

from app.models.refresh_token import RefreshToken

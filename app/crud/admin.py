from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.user import User, UserRole
from app.models.product import Product
from app.models.order import Order
from app.models.payment import SupplierTransaction, TransactionType


def get_admin_summary(db: Session):
    total_clients = db.query(func.count(User.id)).filter(User.role == UserRole.client).scalar()
    total_suppliers = db.query(func.count(User.id)).filter(User.role == UserRole.supplier).scalar()
    total_products = db.query(func.count(Product.id)).scalar()
    total_orders = db.query(func.count(Order.id)).scalar()
    total_revenue = (
        db.query(func.coalesce(func.sum(SupplierTransaction.amount), 0))
        .filter(SupplierTransaction.type == TransactionType.sale)
        .scalar()
    )

    return {
        "total_clients": total_clients,
        "total_suppliers": total_suppliers,
        "total_products": total_products,
        "total_orders": total_orders,
        "total_revenue": float(total_revenue),
    }

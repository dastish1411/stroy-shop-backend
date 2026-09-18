from collections import defaultdict
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.order import Order, SubOrder, OrderItem, SubOrderStatus
from app.models.product import Product
from app.schemas.order import OrderCreate

from decimal import Decimal


def create_order(db: Session, order_data: OrderCreate, user_id: int) -> Order:
    items_by_supplier: dict[int, list[tuple[Product, float]]] = defaultdict(list)

    for item in order_data.items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail=f"Товар с id={item.product_id} не найден")

        if product.quantity < item.quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Недостаточно товара '{product.name}': доступно {product.quantity} {product.unit.value}",
            )

        items_by_supplier[product.supplier_id].append((product, item.quantity))

    new_order = Order(user_id=user_id)
    db.add(new_order)
    db.flush()

    for supplier_id, products_list in items_by_supplier.items():
        sub_order_amount = sum(product.price * Decimal(str(quantity)) for product, quantity in products_list)

        new_sub_order = SubOrder(
            order_id=new_order.id,
            supplier_id=supplier_id,
            amount=sub_order_amount,
        )
        db.add(new_sub_order)
        db.flush()

        for product, quantity in products_list:
            order_item = OrderItem(
                sub_order_id=new_sub_order.id,
                product_id=product.id,
                quantity=quantity,
                price_at_purchase=product.price,
            )
            db.add(order_item)

    db.commit()
    db.refresh(new_order)
    return new_order


def get_orders_by_user(db: Session, user_id: int) -> list[Order]:
    return db.query(Order).filter(Order.user_id == user_id).order_by(Order.created_at.desc()).all()


def get_sub_orders_by_supplier(db: Session, supplier_id: int) -> list[SubOrder]:
    return db.query(SubOrder).filter(SubOrder.supplier_id == supplier_id).order_by(SubOrder.created_at.desc()).all()


def update_sub_order_status(db: Session, sub_order: SubOrder, new_status: SubOrderStatus) -> SubOrder:
    sub_order.status = new_status
    db.commit()
    db.refresh(sub_order)
    return sub_order
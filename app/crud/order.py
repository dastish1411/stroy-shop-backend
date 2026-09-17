from collections import defaultdict
from sqlalchemy.orm import Session
from fastapi import HTTPException
from decimal import Decimal

from app.models.order import Order, SubOrder, OrderItem, SubOrderStatus
from app.models.product import Product
from app.schemas.order import OrderCreate

def create_order(db: Session, order_data: OrderCreate, user_id: int) -> Order:
    # шаг 1: загружаем все товары из запроса и группируем их по поставщику
    # defaultdict(list) - обычный словарь, который сам создаёт пустой список
    # для нового ключа, если его ещё не было (удобно, чтобы не проверять вручную)
    items_by_supplier: dict[int, list[tuple[Product, float]]] = defaultdict(list)

    for item in order_data.items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if not product:
            raise HTTPExepction(status_code=404, detail=f"Товар с id={item.product_id} не найден")

        # шаг 2: сразу проверяем остатки - до того как что-либо создавать в базе
        if product.quantity < item.quantity:
            raise HTTPExepction(
                status_code=400,
                detail=f"Недостаточно товара '{product.name}': доступно {product.quantity} {product.unit.value}",
            )
        items_by_supplier[product.supplier_id].append((product, item.quantity))

    # шаг 3: создаём общий Order
    new_order = Order(user_id=user_id)
    db.add(new_order)
    db.flush() # flush - как commit, но без завершения транзакции,
    # нужен, чтобы получить new_order.id ДО полного сохранения

    # шаг 4: для каждого поставщика создаём отдельный SubOrder
    for supplier_id, products_list in items_by_supplier.items():
        sub_order_amount = sum(product.price * Decimal(str(quantity)) for product, quantity in products_list)

        new_sub_order = SubOrder(
            order_id=new_order.id,
            supplier_id=supplier_id,
            amount=sub_order_amount,
        )
        db.add(new_sub_order)
        db.flush() # получаем new_sub_order.id


        # шаг 5: создаём OrderItem для каждого товара внутри этого под-заказа
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
    # история заказов клиента
    return db.query(Order).filter(Order.user_id == user_id).order_by(Order.created_at.desc()).all()


def get_sub_orders_by_supplier(db: Session, supplier_id: int) -> list[SubOrder]:
    # под-заказы конкретного поставщика - для его личного кабинета
    return db.query(SubOrder).filter(SubOrder.supplier_id == supplier_id).order_by(SubOrder.created_at.desc()).all()


def update_sub_order_status(db: Session, sub_order: SubOrder, new_status: SubOrderStatus) -> SubOrder:
    sub_order.status = new_status
    db.commit()
    db.refresh(sub_order)
    return sub_order
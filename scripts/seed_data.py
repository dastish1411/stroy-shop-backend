"""
Скрипт наполнения базы демонстрационными данными.
Безопасно запускать повторно - пропускает уже существующие записи.
Запуск: docker compose exec backend python3 scripts/seed_data.py
"""
import sys
import os
import random
from datetime import datetime, timedelta, timezone

sys.path.append(os.getcwd())

from app.db.session import SessionLocal
from app.models.user import User, UserRole
from app.models.supplier import Supplier
from app.models.category import Category
from app.models.product import Product, Unit
from app.models.order import Order, SubOrder, OrderItem, SubOrderStatus
from app.models.payment import Payment, PaymentMethod, PaymentStatus, SupplierTransaction, TransactionType
from app.core.security import hash_password


def get_or_create_user(db, email, password, role, full_name=None):
    user = db.query(User).filter(User.email == email).first()
    if user:
        return user

    user = User(
        email=email,
        hashed_password=hash_password(password),
        full_name=full_name,
        role=role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_or_create_supplier(db, owner_id, name):
    supplier = db.query(Supplier).filter(Supplier.owner_id == owner_id).first()
    if supplier:
        return supplier

    supplier = Supplier(owner_id=owner_id, name=name)
    db.add(supplier)
    db.commit()
    db.refresh(supplier)
    return supplier


def get_or_create_product(db, name, category_id, supplier_id, price, quantity, unit, description):
    product = db.query(Product).filter(
        Product.name == name,
        Product.supplier_id == supplier_id,
    ).first()
    if product:
        return product

    product = Product(
        name=name,
        category_id=category_id,
        supplier_id=supplier_id,
        price=price,
        quantity=quantity,
        unit=unit,
        description=description,
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


def create_fake_historical_order(db, client, product, quantity, days_ago):
    fake_date = datetime.now(timezone.utc) - timedelta(days=days_ago)

    order = Order(user_id=client.id, created_at=fake_date)
    db.add(order)
    db.flush()

    amount = product.price * quantity

    sub_order = SubOrder(
        order_id=order.id,
        supplier_id=product.supplier_id,
        amount=amount,
        status=SubOrderStatus.delivered,
        created_at=fake_date,
        updated_at=fake_date,
    )
    db.add(sub_order)
    db.flush()

    order_item = OrderItem(
        sub_order_id=sub_order.id,
        product_id=product.id,
        quantity=quantity,
        price_at_purchase=product.price,
    )
    db.add(order_item)

    if product.quantity >= quantity:
        product.quantity -= quantity

    supplier = db.query(Supplier).filter(Supplier.id == product.supplier_id).first()
    supplier.balance += amount

    transaction = SupplierTransaction(
        supplier_id=supplier.id,
        sub_order_id=sub_order.id,
        amount=amount,
        type=TransactionType.sale,
        balance_after=supplier.balance,
        created_at=fake_date,
    )
    db.add(transaction)

    payment = Payment(
        sub_order_id=sub_order.id,
        user_id=client.id,
        amount=amount,
        method=random.choice([PaymentMethod.card, PaymentMethod.qr]),
        status=PaymentStatus.success,
        created_at=fake_date,
    )
    db.add(payment)

    db.commit()


# варианты названий товаров по категориям - у каждого поставщика будет
# несколько РАЗНЫХ товаров из этого списка в каждой категории
PRODUCT_VARIANTS = {
    "Цемент": [
        "Цемент М400, мешок 50кг",
        "Цемент М500, мешок 50кг",
        "Цемент М600, мешок 50кг",
        "Цемент белый, мешок 25кг",
    ],
    "Кирпич": [
        "Кирпич красный полнотелый",
        "Кирпич силикатный белый",
        "Кирпич облицовочный",
        "Кирпич пустотелый",
    ],
    "Песок": [
        "Песок речной",
        "Песок карьерный",
        "Песок мытый",
        "Песок строительный",
    ],
}

UNITS_BY_CATEGORY = {
    "Цемент": Unit.kg,
    "Кирпич": Unit.piece,
    "Песок": Unit.kg,
}


def main():
    db = SessionLocal()

    print("Проверяем категории...")
    categories = db.query(Category).all()
    category_map = {c.name: c.id for c in categories}
    print(f"  Найдено категорий: {len(categories)}")

    print("\nСоздаём поставщиков (12 штук)...")
    supplier_names = [
        "СтройГарант", "БазаМатериалов", "КровляСервис", "СтройДвор",
        "МастерСтрой", "ПрофСтрой", "СтройОпторг", "ГлавСтройБаза",
        "СтройИмпорт", "БазаКирпича", "ЦементТрейд", "СтройЛогистика",
    ]
    created_suppliers = []
    for i, name in enumerate(supplier_names, start=10):
        email = f"supplier{i}@example.com"
        user = get_or_create_user(db, email, "123", UserRole.supplier)
        supplier = get_or_create_supplier(db, user.id, name)
        created_suppliers.append(supplier)
    print(f"  Готово: {len(created_suppliers)} поставщиков")

    print("\nСоздаём товары (несколько на категорию у каждого поставщика)...")
    created_products = []
    for supplier in created_suppliers:
        for category_name, variants in PRODUCT_VARIANTS.items():
            category_id = category_map.get(category_name)
            if not category_id:
                continue
            unit = UNITS_BY_CATEGORY[category_name]

            # берём 3-4 случайных варианта названия для этого поставщика в этой категории
            chosen_variants = random.sample(variants, k=min(3, len(variants)))
            for name in chosen_variants:
                price = round(random.uniform(280, 420), 2) if category_name == "Цемент" else \
                        round(random.uniform(9, 15), 2) if category_name == "Кирпич" else \
                        round(random.uniform(600, 900), 2)
                quantity = random.randint(1000, 10000)
                product = get_or_create_product(
                    db, name, category_id, supplier.id, price, quantity, unit,
                    f"{name} от компании {supplier.name}",
                )
                created_products.append(product)
    print(f"  Готово: {len(created_products)} товаров")

    print("\nСоздаём клиентов (100 штук)...")
    created_clients = []
    for i in range(1, 101):
        email = f"testclient{i}@example.com"
        user = get_or_create_user(db, email, "123", UserRole.client, full_name=f"Клиент {i}")
        created_clients.append(user)
    print(f"  Готово: {len(created_clients)} клиентов")

    print("\nСоздаём историю продаж для графика (по каждому поставщику)...")
    for supplier in created_suppliers:
        supplier_products = [p for p in created_products if p.supplier_id == supplier.id]
        if not supplier_products:
            continue

        for _ in range(8):
            product = random.choice(supplier_products)
            client = random.choice(created_clients)
            quantity = random.randint(5, 40)
            days_ago = random.randint(0, 29)
            create_fake_historical_order(db, client, product, quantity, days_ago)

    db.close()
    print("\nГотово! База наполнена демонстрационными данными.")


if __name__ == "__main__":
    main()
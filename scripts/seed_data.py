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
        print(f"  Пользователь {email} уже существует, пропускаем")
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
    print(f"  Создан пользователь: {email}")
    return user


def get_or_create_supplier(db, owner_id, name):
    supplier = db.query(Supplier).filter(Supplier.owner_id == owner_id).first()
    if supplier:
        return supplier

    supplier = Supplier(owner_id=owner_id, name=name)
    db.add(supplier)
    db.commit()
    db.refresh(supplier)
    print(f"  Создан профиль поставщика: {name}")
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
    print(f"  Создан товар: {name} ({supplier_id})")
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


def main():
    db = SessionLocal()

    print("Проверяем категории...")
    categories = db.query(Category).all()
    category_map = {c.name: c.id for c in categories}

    print("\nСоздаём поставщиков...")
    suppliers_data = [
        ("supplier4@example.com", "Компания КровляПлюс"),
        ("supplier5@example.com", "СтройБаза Юг"),
    ]
    for email, company_name in suppliers_data:
        user = get_or_create_user(db, email, "123", UserRole.supplier)
        get_or_create_supplier(db, user.id, company_name)

    print("\nСоздаём клиентов...")
    clients_data = ["client2@example.com", "client3@example.com"]
    created_clients = []
    for email in clients_data:
        user = get_or_create_user(db, email, "123", UserRole.client, full_name="Тестовый клиент")
        created_clients.append(user)

    print("\nСоздаём товары для новых поставщиков...")
    products_data = [
        ("Цемент М500, мешок 50кг", "Цемент", 340, 4000, Unit.kg, "Портландцемент М500"),
        ("Кирпич красный полнотелый", "Кирпич", 11.5, 20000, Unit.piece, "Керамический кирпич"),
        ("Песок речной", "Песок", 770, 180000, Unit.kg, "Песок речной мытый"),
    ]
    all_suppliers = db.query(Supplier).all()
    new_supplier_names = ["Компания КровляПлюс", "СтройБаза Юг"]
    for supplier in all_suppliers:
        if supplier.name in new_supplier_names:
            for name, category_name, price, quantity, unit, description in products_data:
                category_id = category_map.get(category_name)
                if category_id:
                    get_or_create_product(
                        db, name, category_id, supplier.id, price, quantity, unit, description
                    )

    print("\nСоздаём растянутую по датам историю продаж для ВСЕХ поставщиков (для графика)...")
    all_products = db.query(Product).all()

    if all_products and created_clients:
        # для КАЖДОГО поставщика создаём 10 исторических заказов,
        # используя только ЕГО СОБСТВЕННЫЕ товары - чтобы у каждой линии
        # на графике было несколько точек, растянутых по последним 30 дням
        for supplier in all_suppliers:
            supplier_products = [p for p in all_products if p.supplier_id == supplier.id]
            if not supplier_products:
                continue

            for _ in range(10):
                product = random.choice(supplier_products)
                client = random.choice(created_clients)
                quantity = random.randint(5, 40)
                days_ago = random.randint(0, 29)
                create_fake_historical_order(db, client, product, quantity, days_ago)

            print(f"  Создано 10 исторических заказов для {supplier.name}")
    else:
        print("  Нет товаров или клиентов для создания истории")

    db.close()
    print("\nГотово!")


if __name__ == "__main__":
    main()
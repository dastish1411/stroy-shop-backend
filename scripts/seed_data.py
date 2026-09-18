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
    # ищем пользователя по email - если уже есть, просто возвращаем его
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
    # проверяем товар именно у ЭТОГО поставщика с ЭТИМ названием
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
    # создаёт заказ и сразу "успешно оплаченный" под-заказ,
    # с датой создания в прошлом - для красивого графика продаж
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

    # списываем товар со склада, как при реальной оплате
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
    if len(categories) < 3:
        print("  Внимание: категорий меньше 3, но по договорённости мы их не создаём здесь")
    category_map = {c.name: c.id for c in categories}

    print("\nСоздаём поставщиков...")
    suppliers_data = [
        ("supplier4@example.com", "Компания КровляПлюс"),
        ("supplier5@example.com", "СтройБаза Юг"),
    ]
    created_suppliers = []
    for email, company_name in suppliers_data:
        user = get_or_create_user(db, email, "123", UserRole.supplier)
        supplier = get_or_create_supplier(db, user.id, company_name)
        created_suppliers.append(supplier)

    print("\nСоздаём клиентов...")
    clients_data = ["client2@example.com", "client3@example.com"]
    created_clients = []
    for email in clients_data:
        user = get_or_create_user(db, email, "123", UserRole.client, full_name="Тестовый клиент")
        created_clients.append(user)

    print("\nСоздаём товары...")
    products_data = [
        ("Цемент М500, мешок 50кг", "Цемент", 340, 4000, Unit.kg, "Портландцемент М500"),
        ("Кирпич красный полнотелый", "Кирпич", 11.5, 20000, Unit.piece, "Керамический кирпич"),
        ("Песок речной", "Песок", 770, 180000, Unit.kg, "Песок речной мытый"),
    ]
    created_products = []
    for supplier in created_suppliers:
        for name, category_name, price, quantity, unit, description in products_data:
            category_id = category_map.get(category_name)
            if not category_id:
                print(f"  Пропускаем товар {name}: категория {category_name} не найдена")
                continue
            product = get_or_create_product(
                db, name, category_id, supplier.id, price, quantity, unit, description
            )
            created_products.append(product)

    print("\nСоздаём историю продаж за последний месяц (для графика)...")
    if created_products and created_clients:
        for _ in range(15):
            product = random.choice(created_products)
            client = random.choice(created_clients)
            quantity = random.randint(5, 50)
            days_ago = random.randint(1, 30)
            create_fake_historical_order(db, client, product, quantity, days_ago)
        print("  Создано 15 исторических заказов")
    else:
        print("  Нет товаров или клиентов для создания истории")

    db.close()
    print("\nГотово!")


if __name__ == "__main__":
    main()

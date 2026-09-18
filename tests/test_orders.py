from conftest import create_admin_directly


def register_and_login(client, email, password="test123", role="client", company_name=None):
    # вспомогательная функция - регистрирует и логинит пользователя, возвращает готовый заголовок с токеном
    payload = {"email": email, "password": password, "role": role}
    if company_name:
        payload["company_name"] = company_name

    client.post("/auth/register", json=payload)
    response = client.post("/auth/login", json={"email": email, "password": password})
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def create_category(client):
    # создаёт тестовую категорию через отдельного admin-пользователя
    create_admin_directly()
    admin_response = client.post("/auth/login", json={
        "email": "admin@example.com",
        "password": "test123",
    })
    admin_headers = {"Authorization": f"Bearer {admin_response.json()['access_token']}"}

    response = client.post("/categories/", json={
        "name": "Категория",
        "image_url": "https://example.com/image.jpg",
    }, headers=admin_headers)
    return response.json()["id"]


def create_product(client, supplier_headers, category_id, price=100, quantity=1000):
    # вспомогательная функция - создаёт товар от имени переданного поставщика
    response = client.post("/supplier/products", json={
        "name": "Товар",
        "category_id": category_id,
        "price": price,
        "quantity": quantity,
        "unit": "kg",
    }, headers=supplier_headers)
    return response.json()


# ПРОВЕРКА: заказ с товарами от РАЗНЫХ поставщиков разбивается на несколько под-заказов
def test_order_splits_by_supplier(client):
    category_id = create_category(client)

    supplier1_headers = register_and_login(
        client, "supplier1@example.com", role="supplier", company_name="Компания 1"
    )
    supplier2_headers = register_and_login(
        client, "supplier2@example.com", role="supplier", company_name="Компания 2"
    )

    product1 = create_product(client, supplier1_headers, category_id, price=100)
    product2 = create_product(client, supplier2_headers, category_id, price=200)

    client_headers = register_and_login(client, "client@example.com", role="client")

    # клиент оформляет ОДИН заказ, но с товарами от ДВУХ разных поставщиков
    response = client.post("/orders/", json={
        "items": [
            {"product_id": product1["id"], "quantity": 10},
            {"product_id": product2["id"], "quantity": 5},
        ]
    }, headers=client_headers)

    # ожидаем успешное оформление заказа
    assert response.status_code == 200
    data = response.json()

    # ГЛАВНАЯ ПРОВЕРКА: заказ ДОЛЖЕН разбиться ровно на 2 под-заказа -
    # по одному на каждого поставщика
    assert len(data["sub_orders"]) == 2

    amounts = sorted([sub["amount"] for sub in data["sub_orders"]])
    # проверяем правильность расчёта сумм: 10 кг * 100 = 1000, 5 кг * 200 = 1000
    assert amounts == [1000, 1000]


# ПРОВЕРКА: нельзя заказать больше товара, чем есть в наличии на складе
def test_order_fails_if_not_enough_stock(client):
    category_id = create_category(client)
    supplier_headers = register_and_login(
        client, "supplier@example.com", role="supplier", company_name="Компания"
    )
    product = create_product(client, supplier_headers, category_id, quantity=5)

    client_headers = register_and_login(client, "client@example.com", role="client")

    # пытаемся заказать 100 кг, хотя на складе всего 5 кг
    response = client.post("/orders/", json={
        "items": [{"product_id": product["id"], "quantity": 100}]
    }, headers=client_headers)

    # ожидаем ошибку "неверный запрос" (код 400), заказ не должен создаться
    assert response.status_code == 400


# ПРОВЕРКА: при оплате товар СПИСЫВАЕТСЯ со склада, а поставщику НАЧИСЛЯЕТСЯ баланс
def test_payment_deducts_stock_and_credits_supplier_balance(client):
    category_id = create_category(client)
    supplier_headers = register_and_login(
        client, "supplier@example.com", role="supplier", company_name="Компания"
    )
    product = create_product(client, supplier_headers, category_id, price=350, quantity=1000)

    client_headers = register_and_login(client, "client@example.com", role="client")

    order_response = client.post("/orders/", json={
        "items": [{"product_id": product["id"], "quantity": 50}]
    }, headers=client_headers)
    sub_order_id = order_response.json()["sub_orders"][0]["id"]

    # клиент оплачивает свой под-заказ картой
    payment_response = client.post(f"/payments/{sub_order_id}", json={
        "method": "card",
    }, headers=client_headers)

    # ожидаем успешную оплату
    assert payment_response.status_code == 200
    # ожидаем статус "успешно" у самого платежа
    assert payment_response.json()["status"] == "success"

    # проверяем, что товар РЕАЛЬНО списался со склада после оплаты
    product_response = client.get(f"/products/{product['id']}")
    assert product_response.json()["quantity"] == 950  # было 1000, заказали 50, осталось 950

    # проверяем, что поставщику РЕАЛЬНО начислился баланс после оплаты
    finance_response = client.get("/payments/supplier/finance", headers=supplier_headers)
    assert finance_response.json()["balance"] == 17500  # 50 кг умножить на 350 сом


# ПРОВЕРКА: клиент НЕ МОЖЕТ оплатить заказ, который оформил ДРУГОЙ клиент
def test_cannot_pay_someone_elses_order(client):
    category_id = create_category(client)
    supplier_headers = register_and_login(
        client, "supplier@example.com", role="supplier", company_name="Компания"
    )
    product = create_product(client, supplier_headers, category_id)

    client1_headers = register_and_login(client, "client1@example.com", role="client")
    client2_headers = register_and_login(client, "client2@example.com", role="client")

    # client1 оформляет заказ
    order_response = client.post("/orders/", json={
        "items": [{"product_id": product["id"], "quantity": 10}]
    }, headers=client1_headers)
    sub_order_id = order_response.json()["sub_orders"][0]["id"]

    # client2 пытается оплатить ЧУЖОЙ заказ (принадлежащий client1)
    response = client.post(f"/payments/{sub_order_id}", json={
        "method": "card",
    }, headers=client2_headers)

    # ожидаем ошибку "доступ запрещён" (код 403)
    assert response.status_code == 403
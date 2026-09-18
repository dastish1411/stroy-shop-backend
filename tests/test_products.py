from conftest import create_admin_directly


def register_and_login_supplier(client, email="supplier@example.com"):
    client.post("/auth/register", json={
        "email": email,
        "password": "test123",
        "role": "supplier",
        "company_name": "Тестовая компания",
    })

    response = client.post("/auth/login", json={
        "email": email,
        "password": "test123",
    })

    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def create_test_category(client):
    create_admin_directly()

    login_response = client.post("/auth/login", json={
        "email": "admin@example.com",
        "password": "test123",
    })
    admin_token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {admin_token}"}

    response = client.post("/categories/", json={
        "name": "Тестовая категория",
        "image_url": "https://example.com/image.jpg",
    }, headers=headers)

    return response.json()["id"]


def test_supplier_can_create_product(client):
    headers = register_and_login_supplier(client)
    category_id = create_test_category(client)

    response = client.post("/supplier/products", json={
        "name": "Тестовый цемент",
        "category_id": category_id,
        "price": 350,
        "quantity": 1000,
        "unit": "kg",
    }, headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Тестовый цемент"
    assert data["price"] == 350


def test_client_cannot_create_product(client):
    client.post("/auth/register", json={
        "email": "client@example.com",
        "password": "test123",
        "role": "client",
    })
    login_response = client.post("/auth/login", json={
        "email": "client@example.com",
        "password": "test123",
    })
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    category_id = create_test_category(client)

    response = client.post("/supplier/products", json={
        "name": "Попытка обмана",
        "category_id": category_id,
        "price": 100,
        "quantity": 10,
        "unit": "kg",
    }, headers=headers)

    assert response.status_code == 403


def test_supplier_cannot_edit_other_suppliers_product(client):
    category_id = create_test_category(client)

    headers1 = register_and_login_supplier(client, email="supplier1@example.com")
    create_response = client.post("/supplier/products", json={
        "name": "Товар поставщика 1",
        "category_id": category_id,
        "price": 100,
        "quantity": 50,
        "unit": "kg",
    }, headers=headers1)
    product_id = create_response.json()["id"]

    headers2 = register_and_login_supplier(client, email="supplier2@example.com")
    response = client.patch(f"/supplier/products/{product_id}", json={
        "price": 999,
    }, headers=headers2)

    assert response.status_code == 403


def test_public_catalog_shows_products_without_auth(client):
    headers = register_and_login_supplier(client)
    category_id = create_test_category(client)

    client.post("/supplier/products", json={
        "name": "Публичный товар",
        "category_id": category_id,
        "price": 200,
        "quantity": 100,
        "unit": "piece",
    }, headers=headers)

    # запрос БЕЗ токена авторизации - публичный каталог должен быть доступен всем
    response = client.get("/products")

    assert response.status_code == 200
    data = response.json()
    # ответ - это объект с пагинацией, сами товары лежат внутри "items"
    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["name"] == "Публичный товар"
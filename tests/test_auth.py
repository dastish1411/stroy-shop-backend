def test_register_new_user(client):
    # отправляем запрос на регистрацию, точно так же, как это делает форма на фронтенде
    response = client.post("/auth/register", json={
        "email": "test@example.com",
        "password": "test123",
        "role": "client",
    })

    # проверяем, что сервер ответил успешно
    assert response.status_code == 200

    # проверяем, что в ответе вернулся правильный email
    data = response.json()
    assert data["email"] == "test@example.com"

    # проверяем, что пароль НИКОГДА не возвращается в ответе -
    # это важная проверка безопасности
    assert "password" not in data
    assert "hashed_password" not in data


def test_register_duplicate_email_fails(client):
    # регистрируем пользователя первый раз - должно получиться
    client.post("/auth/register", json={
        "email": "duplicate@example.com",
        "password": "test123",
        "role": "client",
    })

    # пытаемся зарегистрировать ВТОРОЙ раз с тем же email
    response = client.post("/auth/register", json={
        "email": "duplicate@example.com",
        "password": "test123",
        "role": "client",
    })

    # должна вернуться ошибка, а не успех
    assert response.status_code == 400


def test_register_admin_role_forbidden(client):
    # проверяем ту самую защиту, которую мы добавляли раньше -
    # нельзя зарегистрироваться сразу с ролью admin
    response = client.post("/auth/register", json={
        "email": "hacker@example.com",
        "password": "test123",
        "role": "admin",
    })

    assert response.status_code == 403


def test_login_with_correct_credentials(client):
    # сначала регистрируем пользователя
    client.post("/auth/register", json={
        "email": "login_test@example.com",
        "password": "correct_password",
        "role": "client",
    })

    # пытаемся залогиниться с правильным паролем
    response = client.post("/auth/login", json={
        "email": "login_test@example.com",
        "password": "correct_password",
    })

    assert response.status_code == 200
    data = response.json()
    # проверяем, что вернулись оба токена
    assert "access_token" in data
    assert "refresh_token" in data


def test_login_with_wrong_password_fails(client):
    client.post("/auth/register", json={
        "email": "wrong_pass@example.com",
        "password": "correct_password",
        "role": "client",
    })

    response = client.post("/auth/login", json={
        "email": "wrong_pass@example.com",
        "password": "WRONG_password",
    })

    assert response.status_code == 401

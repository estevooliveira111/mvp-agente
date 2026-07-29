def test_register_returns_access_token(client):
    response = client.post(
        "/api/v1/auth/register",
        json={"external_id": "new-user", "password": "s3cret-pass"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]


def test_register_twice_with_password_returns_409(client):
    client.post(
        "/api/v1/auth/register",
        json={"external_id": "dup-user", "password": "s3cret-pass"},
    )

    response = client.post(
        "/api/v1/auth/register",
        json={"external_id": "dup-user", "password": "another-pass"},
    )

    assert response.status_code == 409


def test_login_with_correct_password_returns_token(client):
    client.post(
        "/api/v1/auth/register",
        json={"external_id": "login-user", "password": "correct-pass"},
    )

    response = client.post(
        "/api/v1/auth/login",
        data={"username": "login-user", "password": "correct-pass"},
    )

    assert response.status_code == 200
    assert response.json()["access_token"]


def test_login_with_wrong_password_returns_401(client):
    client.post(
        "/api/v1/auth/register",
        json={"external_id": "login-user-2", "password": "correct-pass"},
    )

    response = client.post(
        "/api/v1/auth/login",
        data={"username": "login-user-2", "password": "wrong-pass"},
    )

    assert response.status_code == 401


def test_login_with_unknown_user_returns_401(client):
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "ghost-user", "password": "whatever"},
    )

    assert response.status_code == 401


def test_protected_route_without_token_returns_401(client):
    response = client.get("/api/v1/calendar/events")

    assert response.status_code == 401


def test_protected_route_with_invalid_token_returns_401(client):
    response = client.get(
        "/api/v1/calendar/events", headers={"Authorization": "Bearer not-a-real-token"}
    )

    assert response.status_code == 401

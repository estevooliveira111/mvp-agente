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
    response = client.get("/api/v1/chat/sessions")

    assert response.status_code == 401


def test_protected_route_with_invalid_token_returns_401(client):
    response = client.get(
        "/api/v1/chat/sessions", headers={"Authorization": "Bearer not-a-real-token"}
    )

    assert response.status_code == 401


def test_register_existing_bot_user_returns_409(client, db_session):
    from database.user_repository import get_or_create_user

    # Usuário criado por um bot, ainda sem senha.
    get_or_create_user(db_session, "bot-user")

    response = client.post(
        "/api/v1/auth/register",
        json={"external_id": "bot-user", "password": "tomando-a-conta"},
    )

    assert response.status_code == 409


def test_register_rejects_channel_external_id(client):
    response = client.post(
        "/api/v1/auth/register",
        json={"external_id": "telegram:123", "password": "s3cret-pass"},
    )

    assert response.status_code == 422


def test_register_stores_bcrypt_hash(client, db_session):
    from database.models import User

    client.post(
        "/api/v1/auth/register",
        json={"external_id": "bcrypt-user", "password": "s3cret-pass"},
    )

    user = db_session.query(User).filter(User.external_id == "bcrypt-user").first()
    assert user.hashed_password.startswith("$2")
    assert user.password_salt is None


def test_login_migrates_legacy_sha256_password(client, db_session):
    from core.security import SecurityManager
    from database.models import User

    legacy = SecurityManager.hash_sensitive_data("old-pass")
    db_session.add(
        User(external_id="legacy-user", hashed_password=legacy["hash"], password_salt=legacy["salt"])
    )
    db_session.commit()

    response = client.post(
        "/api/v1/auth/login", data={"username": "legacy-user", "password": "old-pass"}
    )

    assert response.status_code == 200
    user = db_session.query(User).filter(User.external_id == "legacy-user").first()
    assert user.password_salt is None
    assert SecurityManager.verify_password("old-pass", user.hashed_password)

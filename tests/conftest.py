import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database.database import Base, get_db
import database.models  # noqa: F401 garante que os models estão registrados no Base.metadata


@pytest.fixture()
def db_engine():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def db_session(db_engine):
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client(db_session):
    import api.routes.auth as auth_route
    import api.routes.calendar as calendar_route
    import api.routes.chat as chat_route

    app = FastAPI()
    app.include_router(auth_route.router)
    app.include_router(calendar_route.router)
    app.include_router(chat_route.router)

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture()
def auth_headers(client):
    """Registra o usuário 'user-1' e devolve o header Authorization já pronto para uso."""
    response = client.post(
        "/api/v1/auth/register",
        json={"external_id": "user-1", "password": "test-password-123"},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def other_user_auth_headers(client):
    """Registra um segundo usuário ('user-2'), usado para testar isolamento entre usuários."""
    response = client.post(
        "/api/v1/auth/register",
        json={"external_id": "user-2", "password": "another-password-456"},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

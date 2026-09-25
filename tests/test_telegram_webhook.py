import pytest
from fastapi.testclient import TestClient

import app as app_module

SECRET_HEADER = "X-Telegram-Bot-Api-Secret-Token"


@pytest.fixture()
def webhook_client():
    # Sem o 'with', o TestClient não dispara o startup (banco, Discord, set_webhook).
    return TestClient(app_module.app)


def test_rejects_update_without_secret(webhook_client, monkeypatch):
    monkeypatch.setattr(app_module.settings, "TELEGRAM_WEBHOOK_SECRET", "segredo-certo")

    response = webhook_client.post("/webhook/telegram", json={"update_id": 1})

    assert response.status_code == 403


def test_rejects_update_with_wrong_secret(webhook_client, monkeypatch):
    monkeypatch.setattr(app_module.settings, "TELEGRAM_WEBHOOK_SECRET", "segredo-certo")

    response = webhook_client.post(
        "/webhook/telegram", json={"update_id": 1}, headers={SECRET_HEADER: "chute"}
    )

    assert response.status_code == 403


def test_rejects_everything_without_secret_outside_development(webhook_client, monkeypatch):
    monkeypatch.setattr(app_module.settings, "TELEGRAM_WEBHOOK_SECRET", "")
    monkeypatch.setattr(app_module.settings, "ENVIRONMENT", "production")

    response = webhook_client.post("/webhook/telegram", json={"update_id": 1})

    assert response.status_code == 403

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


def test_ram_dedup_is_bounded(monkeypatch):
    monkeypatch.setattr(app_module, "PROCESSED_UPDATES_MAX", 3)
    app_module.processed_updates_ram.clear()

    for update_id in ["1", "2", "3", "4"]:
        assert app_module.already_processed_in_ram(update_id) is False

    assert app_module.already_processed_in_ram("4") is True
    assert len(app_module.processed_updates_ram) == 3
    # O mais antigo saiu da janela.
    assert "1" not in app_module.processed_updates_ram

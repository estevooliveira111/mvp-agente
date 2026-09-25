import datetime

from core.account_link import create_link_code, is_link_command, link_command_reply
from database.models import AccountLinkCode


def test_link_sets_password_and_allows_login(client, db_session):
    code = create_link_code(db_session, "telegram:123")

    response = client.post("/api/v1/auth/link", json={"code": code, "password": "nova-senha"})

    assert response.status_code == 200
    assert response.json()["external_id"] == "telegram:123"
    login = client.post("/api/v1/auth/login", data={"username": "telegram:123", "password": "nova-senha"})
    assert login.status_code == 200


def test_link_code_is_single_use(client, db_session):
    code = create_link_code(db_session, "telegram:123")
    client.post("/api/v1/auth/link", json={"code": code, "password": "primeira"})

    response = client.post("/api/v1/auth/link", json={"code": code, "password": "segunda"})

    assert response.status_code == 400


def test_expired_link_code_is_rejected(client, db_session):
    code = create_link_code(db_session, "telegram:123")
    link = db_session.query(AccountLinkCode).one()
    link.expires_at = datetime.datetime.utcnow() - datetime.timedelta(minutes=1)
    db_session.commit()

    response = client.post("/api/v1/auth/link", json={"code": code, "password": "nova-senha"})

    assert response.status_code == 400


def test_new_code_invalidates_previous_one(client, db_session):
    old_code = create_link_code(db_session, "telegram:123")
    create_link_code(db_session, "telegram:123")

    response = client.post("/api/v1/auth/link", json={"code": old_code, "password": "nova-senha"})

    assert response.status_code == 400


def test_wrong_code_is_rejected(client, db_session):
    create_link_code(db_session, "telegram:123")

    response = client.post("/api/v1/auth/link", json={"code": "AAAAAAAAAA", "password": "nova-senha"})

    assert response.status_code == 400


def test_link_command_detection():
    assert is_link_command("/vincular")
    assert is_link_command("  /VINCULAR  ")
    assert is_link_command("/vincular@meu_bot")
    assert not is_link_command("quero vincular minha conta")
    assert not is_link_command("")


def test_link_code_is_not_sent_in_groups():
    reply = link_command_reply("telegram:123", is_private=False)

    assert "privada" in reply

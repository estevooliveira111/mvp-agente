from database.chat_repository import save_message


def test_get_sessions_requires_auth(client):
    response = client.get("/api/v1/chat/sessions")

    assert response.status_code == 401


def test_get_sessions_returns_empty_when_no_sessions(client, auth_headers):
    response = client.get("/api/v1/chat/sessions", headers=auth_headers)

    assert response.status_code == 200
    assert response.json() == []


def test_get_sessions_returns_summary_with_last_message(client, db_session, auth_headers):
    save_message(db_session, "user-1", "session-1", "user", "primeira mensagem")
    save_message(db_session, "user-1", "session-1", "assistant", "última resposta")

    response = client.get("/api/v1/chat/sessions", headers=auth_headers)

    assert response.status_code == 200
    sessions = response.json()
    assert len(sessions) == 1
    assert sessions[0]["session_id"] == "session-1"
    assert sessions[0]["message_count"] == 2
    assert sessions[0]["last_message_preview"] == "última resposta"


def test_get_sessions_truncates_long_preview(client, db_session, auth_headers):
    long_message = "x" * 200
    save_message(db_session, "user-1", "session-1", "user", long_message)

    response = client.get("/api/v1/chat/sessions", headers=auth_headers)

    preview = response.json()[0]["last_message_preview"]
    assert len(preview) == 120


def test_get_sessions_only_returns_own_sessions(
    client, db_session, auth_headers, other_user_auth_headers
):
    save_message(db_session, "user-1", "session-1", "user", "mensagem do user-1")

    response = client.get("/api/v1/chat/sessions", headers=other_user_auth_headers)

    assert response.status_code == 200
    assert response.json() == []


def test_get_session_messages_returns_empty_list_for_new_session(client, auth_headers):
    response = client.get(
        "/api/v1/chat/sessions/does-not-exist/messages", headers=auth_headers
    )

    assert response.status_code == 200
    assert response.json() == []


def test_get_session_messages_returns_persisted_messages(client, db_session, auth_headers):
    save_message(db_session, "user-1", "session-1", "user", "oi")
    save_message(db_session, "user-1", "session-1", "assistant", "olá, tudo bem?")

    response = client.get("/api/v1/chat/sessions/session-1/messages", headers=auth_headers)

    assert response.status_code == 200
    messages = response.json()
    assert [m["content"] for m in messages] == ["oi", "olá, tudo bem?"]


def test_get_session_messages_returns_404_for_another_users_session(
    client, db_session, auth_headers, other_user_auth_headers
):
    save_message(db_session, "user-1", "session-1", "user", "conversa privada")

    response = client.get(
        "/api/v1/chat/sessions/session-1/messages", headers=other_user_auth_headers
    )

    assert response.status_code == 404


def test_send_message_requires_auth(client):
    response = client.post(
        "/api/v1/chat/sessions/session-1/messages", json={"message": "oi"}
    )

    assert response.status_code == 401


def test_send_message_returns_agent_reply(client, auth_headers, monkeypatch):
    import api.routes.chat as chat_route

    monkeypatch.setattr(
        chat_route.manager, "process_message", lambda session_id, user_id, raw_message: "Resposta do agente"
    )

    response = client.post(
        "/api/v1/chat/sessions/session-1/messages",
        json={"message": "Qual a agenda de hoje?"},
        headers=auth_headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["session_id"] == "session-1"
    assert body["reply"] == "Resposta do agente"


def test_send_message_returns_502_when_agent_fails(client, auth_headers, monkeypatch):
    import api.routes.chat as chat_route

    def _raise(*args, **kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(chat_route.manager, "process_message", _raise)

    response = client.post(
        "/api/v1/chat/sessions/session-1/messages",
        json={"message": "oi"},
        headers=auth_headers,
    )

    assert response.status_code == 502

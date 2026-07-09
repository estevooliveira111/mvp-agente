from database.chat_repository import (
    get_or_create_session,
    list_messages_for_session,
    list_sessions_for_user,
    save_message,
)
from database.user_repository import get_or_create_user


def test_get_or_create_session_creates_new_session(db_session):
    user = get_or_create_user(db_session, "user-1")

    session = get_or_create_session(db_session, user, "session-abc")

    assert session.id is not None
    assert session.session_id == "session-abc"
    assert session.user_id == user.id


def test_get_or_create_session_returns_existing_session(db_session):
    user = get_or_create_user(db_session, "user-1")

    first = get_or_create_session(db_session, user, "session-abc")
    second = get_or_create_session(db_session, user, "session-abc")

    assert first.id == second.id


def test_save_message_creates_user_and_session_when_missing(db_session):
    message = save_message(
        db_session,
        external_id="user-1",
        session_id="session-abc",
        role="user",
        content="Olá!",
    )

    assert message.id is not None
    assert message.role == "user"
    assert message.content == "Olá!"
    assert message.metadata_json == {}


def test_save_message_persists_metadata(db_session):
    message = save_message(
        db_session,
        external_id="user-1",
        session_id="session-abc",
        role="assistant",
        content="Resposta",
        metadata={"cost": 0.01},
    )

    assert message.metadata_json == {"cost": 0.01}


def test_list_sessions_for_user_returns_empty_for_unknown_user(db_session):
    assert list_sessions_for_user(db_session, "ghost") == []


def test_list_sessions_for_user_returns_only_own_sessions(db_session):
    save_message(db_session, "user-1", "session-1", "user", "oi")
    save_message(db_session, "user-2", "session-2", "user", "oi")

    sessions = list_sessions_for_user(db_session, "user-1")

    assert len(sessions) == 1
    assert sessions[0].session_id == "session-1"


def test_list_messages_for_session_returns_none_when_session_missing(db_session):
    assert list_messages_for_session(db_session, "does-not-exist") is None


def test_list_messages_for_session_returns_messages_in_order(db_session):
    save_message(db_session, "user-1", "session-1", "user", "primeira")
    save_message(db_session, "user-1", "session-1", "assistant", "segunda")

    messages = list_messages_for_session(db_session, "session-1")

    assert [m.content for m in messages] == ["primeira", "segunda"]

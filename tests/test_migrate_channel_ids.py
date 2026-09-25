from sqlalchemy import text

from database.chat_repository import save_message
from database.migrations.prefix_channel_ids import migrate
from database.models import ChatSessionDB, MessageDB, User


def _external_ids(db):
    return sorted(u.external_id for u in db.query(User).all())


def _session_ids(db):
    return sorted(s.session_id for s in db.query(ChatSessionDB).all())


def test_migrates_legacy_ids_by_channel(db_session):
    save_message(db_session, "123", "123", "user", "telegram privado")
    save_message(db_session, "456", "discord_789", "user", "discord")
    save_message(db_session, "user_terminal", "sessao_cli_local", "user", "cli")

    migrate(db_session)
    db_session.commit()

    assert _external_ids(db_session) == ["cli:terminal", "discord:456", "telegram:123"]
    assert _session_ids(db_session) == ["cli_local", "discord_789", "telegram_123"]


def test_merges_into_ids_created_after_the_change(db_session):
    save_message(db_session, "123", "123", "user", "antiga")
    save_message(db_session, "telegram:123", "telegram_123", "user", "nova")

    migrate(db_session)
    db_session.commit()

    assert _external_ids(db_session) == ["telegram:123"]
    assert _session_ids(db_session) == ["telegram_123"]
    session = db_session.query(ChatSessionDB).one()
    assert session.user.external_id == "telegram:123"
    assert sorted(m.content for m in db_session.query(MessageDB).all()) == ["antiga", "nova"]


def test_keeps_api_users_and_skips_undecidable_ones(db_session):
    db_session.add(User(external_id="999", hashed_password="hash"))
    db_session.add(User(external_id="777"))  # sem sessões: não dá para saber o canal
    db_session.commit()

    report = migrate(db_session)

    assert _external_ids(db_session) == ["777", "999"]
    assert any("777" in line and "PULADO" in line for line in report)


def test_drops_events_table(db_session):
    db_session.execute(text("CREATE TABLE events (id INTEGER)"))

    migrate(db_session, drop_events=True)

    tables = db_session.execute(text("SELECT name FROM sqlite_master WHERE type='table'")).scalars().all()
    assert "events" not in tables

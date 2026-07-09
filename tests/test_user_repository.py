from database.user_repository import get_or_create_user


def test_creates_new_user_when_not_found(db_session):
    user = get_or_create_user(db_session, "user-123", name="Fulano")

    assert user.id is not None
    assert user.external_id == "user-123"
    assert user.name == "Fulano"


def test_returns_existing_user_without_duplicating(db_session):
    first = get_or_create_user(db_session, "user-123", name="Fulano")
    second = get_or_create_user(db_session, "user-123", name="Outro Nome")

    assert first.id == second.id
    # Nome não é sobrescrito ao buscar um usuário já existente.
    assert second.name == "Fulano"


def test_different_external_ids_create_different_users(db_session):
    user_a = get_or_create_user(db_session, "user-a")
    user_b = get_or_create_user(db_session, "user-b")

    assert user_a.id != user_b.id

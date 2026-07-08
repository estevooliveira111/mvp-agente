from typing import List, Optional

from sqlalchemy.orm import Session

from database.models import ChatSessionDB, MessageDB, User


def get_or_create_user(db: Session, external_id: str, name: Optional[str] = None) -> User:
    user = db.query(User).filter(User.external_id == external_id).first()
    if user:
        return user

    user = User(external_id=external_id, name=name)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_or_create_session(db: Session, user: User, session_id: str) -> ChatSessionDB:
    session = db.query(ChatSessionDB).filter(ChatSessionDB.session_id == session_id).first()
    if session:
        return session

    session = ChatSessionDB(session_id=session_id, user_id=user.id)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def save_message(
    db: Session,
    external_id: str,
    session_id: str,
    role: str,
    content: str,
    metadata: Optional[dict] = None,
) -> MessageDB:
    user = get_or_create_user(db, external_id)
    session = get_or_create_session(db, user, session_id)

    message = MessageDB(
        session_id=session.id,
        role=role,
        content=content,
        metadata_json=metadata or {},
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return message


def list_sessions_for_user(db: Session, external_id: str) -> List[ChatSessionDB]:
    user = db.query(User).filter(User.external_id == external_id).first()
    if not user:
        return []

    return (
        db.query(ChatSessionDB)
        .filter(ChatSessionDB.user_id == user.id)
        .order_by(ChatSessionDB.created_at.desc())
        .all()
    )


def list_messages_for_session(db: Session, session_id: str) -> Optional[List[MessageDB]]:
    session = db.query(ChatSessionDB).filter(ChatSessionDB.session_id == session_id).first()
    if not session:
        return None

    return (
        db.query(MessageDB)
        .filter(MessageDB.session_id == session.id)
        .order_by(MessageDB.created_at.asc())
        .all()
    )

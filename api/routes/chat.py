from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database.chat_repository import list_messages_for_session, list_sessions_for_user
from database.database import get_db

router = APIRouter(prefix="/api/v1/chat", tags=["Chat"])


class MessageResponse(BaseModel):
    id: int
    role: str
    content: str
    created_at: datetime

    class Config:
        orm_mode = True


class SessionSummary(BaseModel):
    id: int
    session_id: str
    created_at: datetime
    last_message_at: datetime
    last_message_preview: str
    message_count: int


@router.get("/sessions", response_model=List[SessionSummary])
def get_sessions(external_id: str, db: Session = Depends(get_db)):
    if db is None:
        raise HTTPException(status_code=503, detail="Banco de dados indisponível.")

    sessions = list_sessions_for_user(db, external_id)

    summaries = []
    for session in sessions:
        messages = sorted(session.messages, key=lambda m: m.created_at)
        last_message = messages[-1] if messages else None
        summaries.append(
            SessionSummary(
                id=session.id,
                session_id=session.session_id,
                created_at=session.created_at,
                last_message_at=last_message.created_at if last_message else session.created_at,
                last_message_preview=last_message.content[:120] if last_message else "",
                message_count=len(messages),
            )
        )
    return summaries


@router.get("/sessions/{session_id}/messages", response_model=List[MessageResponse])
def get_session_messages(session_id: str, db: Session = Depends(get_db)):
    if db is None:
        raise HTTPException(status_code=503, detail="Banco de dados indisponível.")

    messages = list_messages_for_session(db, session_id)
    if messages is None:
        raise HTTPException(status_code=404, detail="Sessão de conversa não encontrada.")
    return messages

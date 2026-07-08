from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.agent_bootstrap import manager
from core.logger import logger
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

    # Sessão nova (ainda sem mensagens no banco) retorna lista vazia, não 404 —
    # o front-end usa isso para abrir uma conversa que o usuário acabou de iniciar.
    return list_messages_for_session(db, session_id) or []


class SendMessageRequest(BaseModel):
    external_id: str
    message: str


class SendMessageResponse(BaseModel):
    session_id: str
    reply: str


@router.post("/sessions/{session_id}/messages", response_model=SendMessageResponse)
def send_message(session_id: str, payload: SendMessageRequest):
    """
    Envia uma mensagem em linguagem natural para o agente (mesmo fluxo do Telegram)
    e devolve a resposta já sintetizada. O agente decide sozinho quais ferramentas
    acionar (agenda, e-mail, busca, etc) — o front-end não escolhe uma tool.
    """
    try:
        reply = manager.process_message(
            session_id=session_id,
            user_id=payload.external_id,
            raw_message=payload.message,
        )
    except Exception as e:
        logger.error(f"[Chat API] Falha ao processar mensagem: {e}")
        raise HTTPException(status_code=502, detail="O agente falhou ao processar a mensagem.")

    return SendMessageResponse(session_id=session_id, reply=reply)

from typing import List, Dict
from datetime import datetime
from models.chat import Message, ChatSession
from core.logger import logger

class ConversationMemory:
    """
    Gerencia o histórico de curto prazo das conversas (Context Buffer).
    Mantém o controle do fluxo atual da conversa para a IA não perder o fio da meada.
    """
    def __init__(self):
        # Buffer rápido em memória, usado pelo Context Builder a cada turno.
        # Cada mensagem também é persistida no Postgres (ver _persist) para
        # sobreviver a reinícios e alimentar o histórico exposto pela API de chat.
        self._sessions: Dict[str, ChatSession] = {}

    def add_message(self, session_id: str, user_id: str, message: Message):
        if session_id not in self._sessions:
            self._load(session_id)
        if session_id not in self._sessions:
            self._sessions[session_id] = ChatSession(session_id=session_id, user_id=user_id)

        session = self._sessions[session_id]
        session.messages.append(message)
        session.updated_at = datetime.utcnow()

        self._persist(session_id=session_id, user_id=user_id, message=message)

    def _persist(self, session_id: str, user_id: str, message: Message):
        """Grava a mensagem no banco (best-effort). Falha aqui não pode derrubar a conversa."""
        try:
            from database.database import SessionLocal
            from database.chat_repository import save_message

            if SessionLocal is None:
                return

            db = SessionLocal()
            try:
                save_message(
                    db,
                    external_id=user_id,
                    session_id=session_id,
                    role=message.role,
                    content=message.content,
                    metadata=message.metadata,
                )
            finally:
                db.close()
        except Exception as e:
            logger.error(f"[ConversationMemory] Falha ao persistir mensagem no banco: {e}")
        
    def _load(self, session_id: str) -> None:
        """
        Recarrega do banco uma sessão que não está no buffer (ex: depois de um restart).
        Best-effort: se o banco falhar, a conversa segue sem histórico.
        """
        try:
            from database.database import SessionLocal
            from database.chat_repository import list_messages_for_session
            from database.models import ChatSessionDB

            if SessionLocal is None:
                return

            db = SessionLocal()
            try:
                db_session = db.query(ChatSessionDB).filter(ChatSessionDB.session_id == session_id).first()
                if not db_session:
                    return

                session = ChatSession(session_id=session_id, user_id=db_session.user.external_id)
                for row in list_messages_for_session(db, session_id) or []:
                    session.messages.append(
                        Message(role=row.role, content=row.content, timestamp=row.created_at, metadata=row.metadata_json or {})
                    )
                self._sessions[session_id] = session
            finally:
                db.close()
        except Exception as e:
            logger.error(f"[ConversationMemory] Falha ao recarregar sessão do banco: {e}")

    def get_recent_history(self, session_id: str, limit: int = 10) -> List[Message]:
        """
        Retorna as últimas N mensagens da sessão.
        Isso é crucial para não estourar o limite de tokens (Context Window) do modelo.
        """
        if session_id not in self._sessions:
            self._load(session_id)
        if session_id not in self._sessions:
            return []
        
        # Pega do final (recentes) até o limite
        return self._sessions[session_id].messages[-limit:]
        
    def clear_history(self, session_id: str):
        """Limpa o contexto (útil quando o usuário diz 'esquecer' ou 'reiniciar')."""
        if session_id in self._sessions:
            self._sessions[session_id].messages.clear()
            self._sessions[session_id].updated_at = datetime.utcnow()

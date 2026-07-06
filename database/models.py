import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from database.database import Base

class User(Base):
    """Tabela principal para gerenciar os usuários em todos os canais."""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    # Identificador que vem do canal. Ex: número de telefone do Zap, ou ID do Telegram
    external_id = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relacionamento com as sessões de chat desse usuário
    sessions = relationship("ChatSessionDB", back_populates="user")

class ChatSessionDB(Base):
    """Tabela que agrupa mensagens de uma mesma conversa (Session)."""
    __tablename__ = "chat_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    user = relationship("User", back_populates="sessions")
    messages = relationship("MessageDB", back_populates="session")

class MessageDB(Base):
    """Tabela de Histórico Bruto de Mensagens Relacionais (Logging de conversas)."""
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"))
    
    # 'user', 'assistant', 'system', 'tool'
    role = Column(String, nullable=False)
    
    # O conteúdo da mensagem (texto puro)
    content = Column(Text, nullable=False)
    
    # Metadados opcionais (JSON) para guardar IDs de attachments, custos do LLM, etc.
    metadata_json = Column(JSON, default={})
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    session = relationship("ChatSessionDB", back_populates="messages")

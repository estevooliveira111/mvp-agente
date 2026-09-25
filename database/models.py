import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from database.database import Base

class User(Base):
    """Tabela principal para gerenciar os usuários em todos os canais."""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    # Identificador do usuário. Nos canais vem com prefixo (ex: 'telegram:123', 'discord:456');
    # na API é o nome escolhido no cadastro (sem ':').
    external_id = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=True)

    # Hash bcrypt da senha para login via API (JWT). Fica nulo para usuários criados
    # por um bot (Telegram/Discord): eles não fazem login pela API.
    hashed_password = Column(String, nullable=True)
    # Só preenchido em senhas legadas (SHA-256 + salt); o login migra para bcrypt e zera.
    password_salt = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relacionamento com as sessões de chat desse usuário
    sessions = relationship("ChatSessionDB", back_populates="user")

class AccountLinkCode(Base):
    """
    Código de uso único que um usuário de canal pede ao bot (/vincular) para definir
    uma senha e entrar pela API. Só o hash fica gravado.
    """
    __tablename__ = "account_link_codes"

    id = Column(Integer, primary_key=True, index=True)
    code_hash = Column(String, unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User")

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

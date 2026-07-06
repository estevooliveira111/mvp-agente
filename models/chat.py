from dataclasses import dataclass, field
from typing import List, Dict, Any
from datetime import datetime

@dataclass
class Message:
    """Representa uma única mensagem na conversa (Turno)."""
    role: str  # Exemplos: 'user', 'assistant', 'system', 'tool'
    content: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ChatSession:
    """Representa uma sessão contínua de conversa com um usuário específico."""
    session_id: str
    user_id: str
    messages: List[Message] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

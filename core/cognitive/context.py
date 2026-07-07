from typing import Dict, Any, List
from core.logger import logger

class ContextBuilder:
    """
    Componente responsável por compilar o contexto enviado ao LLM.
    Inclui:
    - Histórico da conversa
    - Informações do usuário / permissões
    - Estado atual e regras do sistema
    """
    
    def __init__(self, memory_client=None):
        self.memory = memory_client
        
    def build_context(self, user_id: str, session_id: str, intent: Dict[str, Any], raw_message: str) -> Dict[str, Any]:
        logger.info("[ContextBuilder] Montando contexto para a execução...")
        
        # Recupera histórico da conversa (Short-term memory)
        recent_history = []
        if self.memory:
            recent_history = self.memory.get_recent_history(session_id)
            
        # No futuro, buscaremos informações de longo prazo (ChromaDB) e do banco (Postgres)
        user_info = {
            "id": user_id,
            "role": "user",
            "permissions": ["all"]
        }
        
        # Monta um pacote de contexto unificado
        context_package = {
            "user_info": user_info,
            "session_id": session_id,
            "recent_history": recent_history,
            "current_message": raw_message,
            "detected_intent": intent
        }
        
        return context_package

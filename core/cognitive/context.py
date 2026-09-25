from typing import Dict, Any, List
from core.logger import logger

class ContextBuilder:
    """
    Componente responsável por compilar o contexto enviado ao LLM.
    Inclui:
    - Histórico da conversa
    - Lembranças de conversas anteriores do mesmo usuário (RAG, ChromaDB)
    - Informações do usuário / permissões
    - Estado atual e regras do sistema
    """
    
    def __init__(self, memory_client=None, vector_memory=None):
        self.memory = memory_client
        self.vector_memory = vector_memory
        
    def build_context(self, user_id: str, session_id: str, intent: Dict[str, Any], raw_message: str) -> Dict[str, Any]:
        logger.info("[ContextBuilder] Montando contexto para a execução...")
        
        # Recupera histórico da conversa (Short-term memory)
        # Vira dict simples: o ReasoningEngine serializa o pacote com json.dumps, e os
        # objetos Message (com datetime) quebravam essa serialização a partir da 2ª mensagem.
        recent_history = []
        if self.memory:
            recent_history = [
                {"role": msg.role, "content": msg.content}
                for msg in self.memory.get_recent_history(session_id)
            ]
            
        # Memória de longo prazo: trocas passadas deste usuário parecidas com a mensagem atual.
        long_term_memories = []
        if self.vector_memory:
            long_term_memories = self.vector_memory.recall(user_id=user_id, query=raw_message)

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
            "long_term_memories": long_term_memories,
            "current_message": raw_message,
            "detected_intent": intent
        }
        
        return context_package

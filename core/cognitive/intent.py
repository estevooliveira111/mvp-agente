from typing import Dict, Any, List
import hashlib
import json
from core.logger import logger
from llm.base import BaseLLM

class IntentDetector:
    """
    Componente responsável por identificar automaticamente:
    - intenção primária
    - objetivo
    - prioridade
    - urgência
    - entidades principais
    - sentimento/emoção
    """
    
    # A intenção só depende do texto da mensagem, então dá para reaproveitar o resultado
    # de mensagens repetidas ("oi", "bom dia") e economizar uma chamada de LLM.
    CACHE_TTL_SECONDS = 3600

    def __init__(self, llm_client: BaseLLM, cache=None):
        self.llm_client = llm_client
        self.cache = cache

    @staticmethod
    def _cache_key(message: str) -> str:
        normalized = " ".join(message.lower().split())
        return "intent:" + hashlib.sha256(normalized.encode("utf-8")).hexdigest()
        
    def detect(self, message: str) -> Dict[str, Any]:
        """
        Analisa a mensagem do usuário e extrai a intenção estruturada.
        """
        logger.info("[IntentDetector] Analisando intenção da mensagem...")

        cache_key = self._cache_key(message)
        if self.cache:
            cached = self.cache.get(cache_key)
            if isinstance(cached, dict):
                logger.info(f"[IntentDetector] Intenção vinda do cache: {cached.get('primary_intent')}")
                return cached
        
        system_prompt = """
Você é um analisador avançado de intenções (Intent Detector).
Sua função é ler a mensagem do usuário e extrair informações cruciais para o sistema de raciocínio.
Retorne um JSON estrito seguindo este schema:

{
  "primary_intent": "NomeDaIntencao. Use exatamente 'Greeting' para saudações e 'SmallTalk' para conversa casual; nos demais casos, algo como 'Info.Query' ou 'Email.Send'",
  "objective": "Descrição curta do objetivo principal",
  "priority": "low | medium | high | critical",
  "urgency": "low | medium | high",
  "emotion": "Sentimento detectado na mensagem (ex: neutral, angry, urgent, happy)",
  "entities": {
     "chave": "valor extraído"
  },
  "requires_action": true/false (Se o usuário quer que uma ação seja feita ou apenas quer conversar)
}
"""
        
        try:
            response = self.llm_client.generate_json(
                prompt=f"Mensagem do usuário: '{message}'\nAnalise e retorne APENAS o JSON.",
                system_prompt=system_prompt
            )
            logger.info(f"[IntentDetector] Intenção detectada: {response.get('primary_intent')} (Ação: {response.get('requires_action')})")
            # Só guarda respostas reais do LLM; o fallback abaixo nunca vai para o cache.
            if self.cache:
                self.cache.set(cache_key, response, ttl_seconds=self.CACHE_TTL_SECONDS)
            return response
        except Exception as e:
            logger.error(f"[IntentDetector] Falha ao detectar intenção: {e}")
            # Fallback seguro
            return {
                "primary_intent": "Unknown",
                "objective": "Compreender a mensagem do usuário",
                "priority": "medium",
                "urgency": "medium",
                "emotion": "neutral",
                "entities": {},
                "requires_action": True
            }

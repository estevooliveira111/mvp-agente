from typing import Dict, Any, List
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
    
    def __init__(self, llm_client: BaseLLM):
        self.llm_client = llm_client
        
    def detect(self, message: str) -> Dict[str, Any]:
        """
        Analisa a mensagem do usuário e extrai a intenção estruturada.
        """
        logger.info("[IntentDetector] Analisando intenção da mensagem...")
        
        system_prompt = """
Você é um analisador avançado de intenções (Intent Detector).
Sua função é ler a mensagem do usuário e extrair informações cruciais para o sistema de racicação.
Retorne um JSON estrito seguindo este schema:

{
  "primary_intent": "NomeDaIntencao (Ex: Calendar.CreateEvent, Info.Query, etc)",
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

from typing import Dict, Any
import json
from core.logger import logger
from llm.base import BaseLLM

class ReasoningEngine:
    """
    O 'Cérebro' do sistema.
    Analisa a intenção e o contexto, decidindo qual estratégia adotar.
    Ele avalia riscos, define prioridades e decide se a tarefa requer planejamento (Planner)
    ou se pode ser resolvida diretamente (Resposta simples).
    """
    def __init__(self, llm_client: BaseLLM):
        self.llm_client = llm_client
        
    def reason(self, context_package: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("[ReasoningEngine] Iniciando processo de raciocínio profundo...")
        
        intent = context_package.get("detected_intent", {})
        
        # Se for uma saudação ou bate-papo básico sem ação necessária, podemos pular planejamento complexo.
        if not intent.get("requires_action") and intent.get("primary_intent") in ["Greeting", "SmallTalk"]:
            logger.info("[ReasoningEngine] Decisão rápida: Bate-papo simples detectado. Rota direta.")
            return {
                "decision": "direct_response",
                "reasoning": "Usuário está apenas conversando.",
                "delegated_to": None
            }
            
        # Caso precise de ação, o Reasoning Engine formula a estratégia macro.
        system_prompt = """
Você é o Motor de Raciocínio (Reasoning Engine) principal de uma Plataforma Multi-Agente.
Você recebeu o contexto e a intenção de uma mensagem do usuário.
Sua tarefa é analisar o problema, quebrar em alto nível, avaliar riscos e decidir a rota de execução.

Rotas possíveis:
1. 'planner': Para tarefas que requerem uso de ferramentas, buscas, banco de dados ou passos múltiplos.
2. 'direct_response': Para respostas diretas (ex: tirar dúvida de conhecimento geral sem usar ferramentas).

Retorne um JSON estrito:
{
  "decision": "planner" ou "direct_response",
  "reasoning": "Sua lógica do porquê essa decisão foi tomada",
  "estimated_complexity": "low" | "medium" | "high",
  "macro_steps": ["passo 1", "passo 2", "..."] (Se for planner)
}
"""
        
        prompt = f"Contexto do problema:\n{json.dumps(context_package, indent=2, ensure_ascii=False)}"
        
        try:
            response = self.llm_client.generate_json(prompt=prompt, system_prompt=system_prompt)
            logger.info(f"[ReasoningEngine] Decisão tomada: Rota {response.get('decision')}, Complexidade: {response.get('estimated_complexity')}")
            return response
        except Exception as e:
            logger.error(f"[ReasoningEngine] Falha no raciocínio: {e}")
            return {
                "decision": "planner",
                "reasoning": "Fallback devido a erro de inferência. Enviando para o Planner por segurança.",
                "estimated_complexity": "high",
                "macro_steps": []
            }

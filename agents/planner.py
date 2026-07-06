import json
from core.logger import logger
from agents.prompts import SYSTEM_PROMPT_PLANNER

class PlannerAgent:
    """
    Sub-agente analítico. Em um padrão LangChain/CrewAI, ele é a etapa de 'Reasoning' (Pensamento).
    Recebe o pedido e o catálogo de ferramentas, e responde com um plano passo-a-passo no formato JSON.
    """
    def __init__(self, llm_client):
        # Cliente do LLM injetado via construtor (ex: google-generativeai)
        self.llm = llm_client
        
    def create_plan(self, objective: str, available_tools_metadata: list) -> dict:
        """
        Pede ao LLM para estruturar como resolver o objetivo usando as ferramentas fornecidas.
        Retorna um dicionário (JSON parseado).
        """
        logger.info(f"[Planner Agent] Criando plano para o objetivo: {objective}")
        
        # ==========================================
        # MVP: Simulação do raciocínio estruturado
        # Aqui você faria a chamada real para: self.llm.generate_content(prompt, response_format='json')
        # ==========================================
        
        # Exemplo do que o LLM retornaria como um plano perfeito:
        plan = {
            "objective": objective,
            "estimated_complexity": "Alta",
            "steps": [
                {
                    "step_number": 1,
                    "action": "Buscar informações mais recentes na web",
                    "tool": "web_search",
                    "arguments": {"query": objective}
                }
            ]
        }
        
        logger.debug(f"[Planner Agent] Plano gerado com {len(plan['steps'])} passos.")
        return plan

import json
from core.logger import logger
from agents.prompts import SYSTEM_PROMPT_EXECUTOR

class ExecutorAgent:
    """
    Sub-agente físico (Action).
    Ele é o 'motor' que de fato importa e roda as funções Python da pasta tools/.
    Em seguida, ele pode (opcionalmente) passar o resultado bruto pro LLM resumir, ou apenas devolver ao Manager.
    """
    def __init__(self, tools_registry: dict):
        # Recebe um mapeamento {"nome_da_tool": funcao_execute_da_tool}
        # ex: {"web_search": web_search.execute}
        self.tools = tools_registry
        
    def execute_step(self, tool_name: str, arguments: dict) -> str:
        """
        Chama fisicamente o código Python da ferramenta solicitada no Plano.
        """
        logger.info(f"[Executor Agent] Acionando ferramenta '{tool_name}'...")
        
        if tool_name not in self.tools:
            error_msg = f"Ferramenta '{tool_name}' não encontrada no catálogo (Registry)."
            logger.error(error_msg)
            return json.dumps({"status": "error", "message": error_msg})
            
        try:
            # Invoca a ferramenta de forma agnóstica passando os argumentos que o Planner gerou
            tool_func = self.tools[tool_name]
            
            # As nossas ferramentas sempre retornam uma string formatada em JSON (sucesso ou erro)
            raw_result = tool_func(**arguments)
            
            logger.debug(f"[Executor Agent] Ferramenta '{tool_name}' retornou com sucesso.")
            return raw_result
            
        except Exception as e:
            logger.error(f"[Executor Agent] Exceção crítica rodando a ferramenta '{tool_name}': {e}")
            return json.dumps({"status": "error", "message": f"Falha na execução Python: {str(e)}"})

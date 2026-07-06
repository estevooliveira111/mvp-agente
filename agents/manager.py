from core.logger import logger
from memory.conversation import ConversationMemory
from agents.planner import PlannerAgent
from agents.executor import ExecutorAgent
from agents.prompts import SYSTEM_PROMPT_MANAGER

class ManagerAgent:
    """
    O Orquestrador (Maestro).
    Ele recebe a mensagem já tratada do Gateway (Channels), carrega o histórico do usuário (Memória),
    decide se aciona o Planner+Executor, junta tudo e formula a resposta final.
    """
    def __init__(self, llm_client, memory: ConversationMemory, planner: PlannerAgent, executor: ExecutorAgent):
        self.llm = llm_client
        self.memory = memory
        self.planner = planner
        self.executor = executor
        
    def process_message(self, session_id: str, user_id: str, raw_message: str) -> str:
        """Fluxo de vida principal de uma interação da Inteligência Artificial."""
        logger.info(f"[Manager Agent] Processando nova mensagem na sessão {session_id} do usuário {user_id}")
        
        # 1. Carrega o contexto passado para não sofrer de amnésia
        history = self.memory.get_recent_history(session_id=session_id)
        
        # 2. (Pipeline Opcional) Pergunta ao LLM se ele consegue responder direto ou se precisa de um plano
        needs_tools = True # Simulando que ele decidiu usar ferramentas
        
        if needs_tools:
            # 3. Aciona o sub-agente analítico
            plan = self.planner.create_plan(objective=raw_message, available_tools_metadata=[])
            
            results_buffer = []
            
            # 4. Aciona o sub-agente físico iterando pelos passos
            for step in plan.get("steps", []):
                t_name = step.get("tool")
                t_args = step.get("arguments", {})
                
                if t_name:
                    step_result = self.executor.execute_step(tool_name=t_name, arguments=t_args)
                    results_buffer.append(f"Resultado da tool {t_name}: {step_result}")
            
            # 5. O Manager junta as descobertas das ferramentas (Context Injection)
            final_context = "\n".join(results_buffer)
            logger.debug("[Manager Agent] Injetando resultados das ferramentas no prompt final.")
            
        # 6. Gera a resposta de fato usando o LLM (com o SYSTEM_PROMPT_MANAGER, history, context e a message)
        final_response = "Esta é uma resposta gerada pelo Manager Agent após coordenar o Planner e o Executor."
        
        # 7. Salva o turno atual na memória
        # self.memory.add_message(...)
        
        return final_response

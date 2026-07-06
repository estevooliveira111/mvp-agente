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
    def __init__(self, llm_client, memory: ConversationMemory, planner: PlannerAgent, executor: ExecutorAgent, tools_metadata: list = None):
        self.llm = llm_client
        self.memory = memory
        self.planner = planner
        self.executor = executor
        self.tools_metadata = tools_metadata or []
        
    def process_message(self, session_id: str, user_id: str, raw_message: str) -> str:
        """Fluxo de vida principal de uma interação da Inteligência Artificial."""
        logger.info(f"[Manager Agent] Processando nova mensagem na sessão {session_id} do usuário {user_id}")
        
        # 1. Carrega o contexto (As 10 últimas mensagens dessa sessão)
        history = self.memory.get_recent_history(session_id=session_id)
        
        # 2. O Planner desenha o plano tático recebendo o catálogo de ferramentas real
        plan = self.planner.create_plan(objective=raw_message, available_tools_metadata=self.tools_metadata)
        
        results_buffer = []
        
        # 3. O Executor percorre passo-a-passo fisicamente
        for step in plan.get("steps", []):
            t_name = step.get("tool")
            t_args = step.get("arguments", {})
            
            if t_name:
                step_result = self.executor.execute_step(tool_name=t_name, arguments=t_args)
                results_buffer.append(f"-> Ação executada: {step.get('action')}\n-> Retorno da tool '{t_name}': {step_result}")
        
        # 4. Injeção de Contexto para a Geração Final
        context_str = "\n".join(results_buffer) if results_buffer else "Nenhuma ferramenta extra foi acionada."
        
        final_prompt = f"""
        MENSAGEM ATUAL DO USUÁRIO: "{raw_message}"
        
        DADOS OBTIDOS PELAS FERRAMENTAS DE APOIO NESTE TURNO (Considere como verdadeiros):
        {context_str}
        
        Utilizando os dados acima (se houverem) e o histórico da conversa, forneça sua resposta final e polida para o usuário.
        Se houve erros na execução da ferramenta, avise o usuário educadamente.
        """
        
        logger.debug("[Manager Agent] Invocando LLM para síntese final da resposta...")
        
        # 5. O Manager sintetiza tudo usando a IA e a persona original dele
        final_response = self.llm.generate_text(
            prompt=final_prompt,
            system_prompt=SYSTEM_PROMPT_MANAGER,
            history=history
        )
        
        # 6. Salva as duas pontas da conversa na memória (Curto prazo / Redis)
        self.memory.add_message(session_id=session_id, role="user", content=raw_message)
        self.memory.add_message(session_id=session_id, role="assistant", content=final_response)
        
        return final_response

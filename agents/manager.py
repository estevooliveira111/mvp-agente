from core.formatting import strip_markdown
from core.logger import logger
from memory.conversation import ConversationMemory
from agents.planner import PlannerAgent
from agents.executor import ExecutorAgent
from models.chat import Message
from agents.prompts import SYSTEM_PROMPT_MANAGER

from core.cognitive.intent import IntentDetector
from core.cognitive.context import ContextBuilder
from core.cognitive.reasoning import ReasoningEngine

class ManagerAgent:
    """
    O Orquestrador (Maestro) atualizado com a Camada Cognitiva (Reasoning Engine).
    """
    def __init__(
        self,
        llm_client,
        memory: ConversationMemory,
        planner: PlannerAgent,
        executor: ExecutorAgent,
        tools_metadata: list = None,
        vector_memory=None,
        cache=None,
    ):
        self.llm = llm_client
        self.memory = memory
        self.planner = planner
        self.executor = executor
        self.tools_metadata = tools_metadata or []
        # Lista das ferramentas para a resposta final. Sem ela, o LLM não sabe o que o
        # agente faz de verdade e responde "o que você sabe fazer?" com generalidades.
        self.capabilities_str = self._describe_capabilities(self.tools_metadata)
        # Memória de longo prazo (ChromaDB) e cache (Memcached). Opcionais: sem eles,
        # o agente funciona só com o histórico recente.
        self.vector_memory = vector_memory
        
        # Inicializa a camada cognitiva
        self.intent_detector = IntentDetector(llm_client=self.llm, cache=cache)
        self.context_builder = ContextBuilder(memory_client=self.memory, vector_memory=vector_memory)
        self.reasoning_engine = ReasoningEngine(llm_client=self.llm)
        
    @staticmethod
    def _describe_capabilities(tools_metadata: list) -> str:
        lines = [
            f"- {tool.get('name')}: {tool.get('description', '')}"
            for tool in tools_metadata
            if tool.get("name")
        ]
        return "\n".join(lines) or "- Nenhuma ferramenta carregada: só conversar e responder perguntas."

    def process_message(self, session_id: str, user_id: str, raw_message: str) -> str:
        """Fluxo de vida principal de uma interação com a nova arquitetura cognitiva."""
        logger.info(f"[Manager Agent] Processando nova mensagem na sessão {session_id} do usuário {user_id}")
        
        # 1. Detecção Automática de Intenção
        intent_data = self.intent_detector.detect(raw_message)
        
        # 2. Construção do Contexto Enriquecido
        context_package = self.context_builder.build_context(
            user_id=user_id,
            session_id=session_id,
            intent=intent_data,
            raw_message=raw_message
        )
        
        # 3. Motor de Raciocínio avalia se precisa planejar ou apenas responder
        reasoning_result = self.reasoning_engine.reason(context_package)
        decision = reasoning_result.get("decision", "direct_response")
        
        history_objects = self.memory.get_recent_history(session_id=session_id)
        history = [{"role": msg.role, "content": msg.content} for msg in history_objects]
        long_term_memories = context_package.get("long_term_memories", [])
        
        results_buffer = []
        
        # 4. Delegação baseada na decisão
        if decision == "planner":
            logger.info("[Manager Agent] Delegando para o Planner realizar tarefas complexas.")
            # Passamos a intenção como objetivo para o planner para maior contexto
            objective = intent_data.get("objective", raw_message)
            plan = self.planner.create_plan(
                objective=objective,
                available_tools_metadata=self.tools_metadata,
                raw_message=raw_message,
                history=history,
                memories=long_term_memories,
            )
            
            for step in plan.get("steps", []):
                t_name = step.get("tool")
                t_args = step.get("arguments", {})
                
                if t_name:
                    step_result = self.executor.execute_step(tool_name=t_name, arguments=t_args)
                    results_buffer.append(f"-> Ação executada: {step.get('action')}\n-> Retorno da tool '{t_name}': {step_result}")
        else:
            logger.info("[Manager Agent] Rota rápida (direct_response). Nenhuma ferramenta será acionada.")
        
        # 5. Injeção de Contexto para a Geração Final
        context_str = "\n".join(results_buffer) if results_buffer else "Nenhuma ferramenta extra foi acionada."
        memories_str = "\n".join(long_term_memories) if long_term_memories else "Nenhuma lembrança relevante."
        
        final_prompt = f"""
        MENSAGEM ATUAL DO USUÁRIO: "{raw_message}"
        
        INTENÇÃO DETECTADA: {intent_data.get("primary_intent")} (Emoção: {intent_data.get("emotion")})

        O QUE VOCÊ CONSEGUE FAZER (ferramentas disponíveis; descreva-as em linguagem simples, sem os nomes técnicos):
        {self.capabilities_str}
        Observação: e-mails e mensagens do Telegram só podem ir para destinatários liberados pelo dono do sistema.

        LEMBRANÇAS DE CONVERSAS ANTERIORES COM ESTE USUÁRIO (use só se forem relevantes):
        {memories_str}
        
        DADOS OBTIDOS PELAS FERRAMENTAS DE APOIO NESTE TURNO (Considere como verdadeiros):
        {context_str}
        
        Utilizando os dados acima (se houverem) e o histórico da conversa, responda ao usuário seguindo as regras do sistema
        (texto simples sem Markdown, sem falar do funcionamento interno, sem frases genéricas).
        Se houve erros na execução da ferramenta, avise o usuário.
        """
        
        logger.debug("[Manager Agent] Invocando LLM para síntese final da resposta...")
        
        final_response = strip_markdown(self.llm.generate_text(
            prompt=final_prompt,
            system_prompt=SYSTEM_PROMPT_MANAGER,
            history=history
        ))
        
        # 6. Salva as duas pontas da conversa na memória
        self.memory.add_message(session_id=session_id, user_id=user_id, message=Message(role="user", content=raw_message))
        self.memory.add_message(session_id=session_id, user_id=user_id, message=Message(role="assistant", content=final_response))
        if self.vector_memory:
            self.vector_memory.remember_exchange(
                user_id=user_id, session_id=session_id, user_message=raw_message, assistant_message=final_response
            )
        
        return final_response

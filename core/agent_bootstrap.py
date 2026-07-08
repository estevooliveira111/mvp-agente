"""
Instâncias singleton do núcleo de IA (LLM, memória, planner, executor, manager).

Centralizado aqui para que tanto o gateway de webhooks (app.py) quanto as rotas
de API (ex: api/routes/chat.py) compartilhem a mesma instância do ManagerAgent
e, portanto, o mesmo estado de memória de conversa.
"""
from llm.factory import get_active_llm
from memory.conversation import ConversationMemory
from agents.planner import PlannerAgent
from agents.executor import ExecutorAgent
from agents.manager import ManagerAgent
from tools.registry import load_all_tools

llm = get_active_llm()
memory = ConversationMemory()
planner = PlannerAgent(llm_client=llm)

tools_registry, tools_metadata = load_all_tools()
executor = ExecutorAgent(tools_registry=tools_registry)

manager = ManagerAgent(llm, memory, planner, executor, tools_metadata=tools_metadata)

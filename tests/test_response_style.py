from agents.manager import ManagerAgent
from agents.prompts import SYSTEM_PROMPT_MANAGER
from core.formatting import strip_markdown
from memory.conversation import ConversationMemory

PASTED_REPLY = """Eu sou um assistente virtual projetado para ajudar você com diversas tarefas! Posso:

*   **Entender e responder** às suas perguntas.
*   **Planejar e executar tarefas complexas** que envolvam busca de informações.

## Resumo
Use `web_search` para *buscas* rápidas."""


def test_strip_markdown_turns_reply_into_plain_text():
    result = strip_markdown(PASTED_REPLY)

    assert "*" not in result and "#" not in result and "`" not in result
    assert "- Entender e responder às suas perguntas." in result
    assert "Use web_search para buscas rápidas." in result


def test_strip_markdown_keeps_plain_text_and_math():
    assert strip_markdown("2 * 3 = 6 e 4 * 5 = 20") == "2 * 3 = 6 e 4 * 5 = 20"
    assert strip_markdown("- item já em texto simples") == "- item já em texto simples"


def test_final_prompt_lists_real_tools_and_reply_is_plain_text():
    captured = {}

    class FakeLLM:
        def generate_json(self, prompt, system_prompt=None):
            return {"primary_intent": "Info.Query", "requires_action": False}

        def generate_text(self, prompt, system_prompt=None, history=None):
            captured["prompt"] = prompt
            captured["system"] = system_prompt
            return "**Posso** buscar na web."

    class FakeReasoning:
        def reason(self, context_package):
            return {"decision": "direct_response"}

    memory = ConversationMemory()
    memory._persist = lambda **kwargs: None
    memory._load = lambda session_id: None
    tools = [{"name": "web_search", "description": "Busca informações externas na web."}]
    manager = ManagerAgent(FakeLLM(), memory, planner=None, executor=None, tools_metadata=tools)
    manager.reasoning_engine = FakeReasoning()

    reply = manager.process_message("s1", "u1", "O que você pode fazer?")

    assert "web_search: Busca informações externas na web." in captured["prompt"]
    assert reply == "Posso buscar na web."


def test_system_prompt_forbids_talking_about_internals_and_markdown():
    assert "Manager Agent" not in SYSTEM_PROMPT_MANAGER
    assert "sub-agentes" in SYSTEM_PROMPT_MANAGER  # só na regra que proíbe mencioná-los
    assert "sem Markdown" in SYSTEM_PROMPT_MANAGER

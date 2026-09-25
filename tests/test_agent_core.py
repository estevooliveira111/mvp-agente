import json
from types import SimpleNamespace

import pytest
from sqlalchemy.orm import sessionmaker

from core.cognitive.context import ContextBuilder
from core.exceptions import LLMException
from database.chat_repository import save_message
from memory.conversation import ConversationMemory
from models.chat import Message


def test_context_package_is_json_serializable_with_history():
    memory = ConversationMemory()
    memory._persist = lambda **kwargs: None
    memory._load = lambda session_id: None
    memory.add_message("s1", "u1", Message(role="user", content="oi"))
    memory.add_message("s1", "u1", Message(role="assistant", content="olá"))

    package = ContextBuilder(memory_client=memory).build_context("u1", "s1", {}, "tudo bem?")

    # O ReasoningEngine faz exatamente isso com o pacote.
    json.dumps(package, ensure_ascii=False)
    assert package["recent_history"] == [
        {"role": "user", "content": "oi"},
        {"role": "assistant", "content": "olá"},
    ]


def test_memory_reloads_history_from_database(db_engine, db_session, monkeypatch):
    import database.database as database_module

    save_message(db_session, "telegram:1", "telegram_1", "user", "mensagem antiga")
    save_message(db_session, "telegram:1", "telegram_1", "assistant", "resposta antiga")
    monkeypatch.setattr(database_module, "SessionLocal", sessionmaker(bind=db_engine))

    # Memória nova = processo recém-reiniciado.
    history = ConversationMemory().get_recent_history("telegram_1")

    assert [m.content for m in history] == ["mensagem antiga", "resposta antiga"]


def test_planner_prompt_has_original_message_history_and_date():
    from agents.planner import PlannerAgent

    captured = {}

    class FakeLLM:
        def generate_json(self, prompt, system_prompt=None):
            captured["prompt"] = prompt
            return {"steps": []}

    PlannerAgent(FakeLLM()).create_plan(
        objective="Enviar e-mail",
        available_tools_metadata=[],
        raw_message="Manda um e-mail pro joao@exemplo.com dizendo que atraso 10 min",
        history=[{"role": "user", "content": "lembra do João?"}],
    )

    prompt = captured["prompt"]
    assert "joao@exemplo.com" in prompt
    assert "lembra do João?" in prompt
    assert "DATA E HORA ATUAIS" in prompt


def _fake_anthropic_response(stop_reason, blocks):
    return SimpleNamespace(stop_reason=stop_reason, content=blocks)


def test_anthropic_returns_only_text_blocks(monkeypatch):
    from llm.anthropic import AnthropicLLM

    llm = AnthropicLLM()
    response = _fake_anthropic_response(
        "end_turn",
        [SimpleNamespace(type="thinking", thinking=""), SimpleNamespace(type="text", text="Olá!")],
    )
    monkeypatch.setattr(llm.client.beta.messages, "create", lambda **kwargs: response)

    assert llm.generate_text("oi") == "Olá!"


def test_anthropic_refusal_raises(monkeypatch):
    from llm.anthropic import AnthropicLLM

    llm = AnthropicLLM()
    monkeypatch.setattr(
        llm.client.beta.messages, "create", lambda **kwargs: _fake_anthropic_response("refusal", [])
    )

    with pytest.raises(LLMException):
        llm.generate_text("oi")


def test_anthropic_invalid_json_raises(monkeypatch):
    from llm.anthropic import AnthropicLLM

    llm = AnthropicLLM()
    response = _fake_anthropic_response("end_turn", [SimpleNamespace(type="text", text="não é json")])
    monkeypatch.setattr(llm.client.beta.messages, "create", lambda **kwargs: response)

    with pytest.raises(LLMException):
        llm.generate_json("me dê um json")


def test_manager_does_not_save_llm_error_as_assistant_reply():
    from agents.manager import ManagerAgent

    class FailingLLM:
        def generate_json(self, prompt, system_prompt=None):
            return {"primary_intent": "Greeting", "requires_action": False}

        def generate_text(self, prompt, system_prompt=None, history=None):
            raise LLMException("API fora do ar")

    memory = ConversationMemory()
    memory._persist = lambda **kwargs: None
    memory._load = lambda session_id: None
    manager = ManagerAgent(FailingLLM(), memory, planner=None, executor=None)

    with pytest.raises(LLMException):
        manager.process_message("s1", "u1", "oi")

    assert memory.get_recent_history("s1") == []

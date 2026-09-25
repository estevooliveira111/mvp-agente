from agents.manager import ManagerAgent
from core.cognitive.context import ContextBuilder
from core.cognitive.intent import IntentDetector
from core.identity import conversation_session_id
from memory.conversation import ConversationMemory
from memory.vector import VectorMemory


class FakeCollection:
    """Imita a coleção do ChromaDB: guarda documentos e filtra por metadados."""

    def __init__(self, distance=0.5):
        self.docs = []
        self.distance = distance

    def add(self, ids, documents, metadatas):
        self.docs.extend(zip(documents, metadatas))

    def query(self, query_texts, n_results, where, include):
        matches = [(d, m) for d, m in self.docs if all(m.get(k) == v for k, v in where.items())][:n_results]
        return {
            "documents": [[d for d, _ in matches]],
            "metadatas": [[m for _, m in matches]],
            "distances": [[self.distance] * len(matches)],
        }


def _vector_memory(collection):
    vector = VectorMemory()
    vector._collection = collection
    return vector


def _conversation_memory():
    memory = ConversationMemory()
    memory._persist = lambda **kwargs: None
    memory._load = lambda session_id: None
    return memory


class FakeCache:
    def __init__(self):
        self.data = {}

    def get(self, key):
        return self.data.get(key)

    def set(self, key, value, ttl_seconds=3600):
        self.data[key] = value


def test_recall_only_returns_memories_of_the_same_user():
    vector = _vector_memory(FakeCollection())
    vector.remember_exchange("telegram:1", "telegram_1", "meu cachorro se chama Rex", "Que nome legal!")
    vector.remember_exchange("telegram:2", "telegram_2", "meu gato se chama Tom", "Bonito!")

    memories = vector.recall("telegram:1", "como se chama meu cachorro?")

    assert len(memories) == 1
    assert "Rex" in memories[0]


def test_recall_ignores_distant_memories():
    vector = _vector_memory(FakeCollection(distance=VectorMemory.MAX_DISTANCE + 0.1))
    vector.remember_exchange("u1", "s1", "algo sem relação", "ok")

    assert vector.recall("u1", "outra coisa") == []


def test_vector_memory_without_chromadb_returns_nothing(monkeypatch):
    vector = VectorMemory()
    # Simula o ChromaDB fora do ar: nenhuma tentativa de conexão até o próximo retry.
    vector._next_attempt = float("inf")

    vector.remember_exchange("u1", "s1", "oi", "olá")
    assert vector.recall("u1", "oi") == []


def test_context_package_includes_long_term_memories():
    vector = _vector_memory(FakeCollection())
    vector.remember_exchange("u1", "s-antiga", "moro em Recife", "Anotado!")

    package = ContextBuilder(_conversation_memory(), vector).build_context("u1", "s-nova", {}, "onde eu moro?")

    assert "Recife" in package["long_term_memories"][0]


def test_manager_saves_exchange_and_uses_memories_in_final_prompt():
    collection = FakeCollection()
    vector = _vector_memory(collection)
    vector.remember_exchange("u1", "s-antiga", "moro em Recife", "Anotado!")
    captured = {}

    class FakeLLM:
        def generate_json(self, prompt, system_prompt=None):
            return {"primary_intent": "Info.Query", "requires_action": False}

        def generate_text(self, prompt, system_prompt=None, history=None):
            captured["prompt"] = prompt
            return "Você mora em Recife."

    class FakeReasoning:
        def reason(self, context_package):
            return {"decision": "direct_response"}

    manager = ManagerAgent(FakeLLM(), _conversation_memory(), planner=None, executor=None, vector_memory=vector)
    manager.reasoning_engine = FakeReasoning()

    manager.process_message("s-nova", "u1", "onde eu moro?")

    assert "moro em Recife" in captured["prompt"]
    assert "Você mora em Recife." in collection.docs[-1][0]


def test_intent_is_cached_by_message_text():
    calls = []

    class FakeLLM:
        def generate_json(self, prompt, system_prompt=None):
            calls.append(prompt)
            return {"primary_intent": "Greeting", "requires_action": False}

    detector = IntentDetector(FakeLLM(), cache=FakeCache())

    first = detector.detect("Bom dia")
    second = detector.detect("  bom   DIA ")

    assert first == second
    assert len(calls) == 1


def test_intent_fallback_is_not_cached():
    cache = FakeCache()

    class FailingLLM:
        def generate_json(self, prompt, system_prompt=None):
            raise RuntimeError("fora do ar")

    IntentDetector(FailingLLM(), cache=cache).detect("oi")

    assert cache.data == {}


def test_group_sessions_are_per_member():
    assert conversation_session_id("telegram", 123, 123, is_private=True) == "telegram_123"
    assert conversation_session_id("telegram", -100, 1, is_private=False) == "telegram_-100_1"
    assert conversation_session_id("telegram", -100, 2, is_private=False) == "telegram_-100_2"

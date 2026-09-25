import threading
import time
import uuid
from datetime import datetime
from typing import List, Optional

from core.config import settings
from core.logger import logger


class VectorMemory:
    """
    Memória de Longo Prazo da IA (RAG) no ChromaDB.

    Cada troca (mensagem do usuário + resposta) vira um documento com o user_id nos
    metadados. A cada nova mensagem, o ContextBuilder busca as trocas passadas mais
    parecidas daquele mesmo usuário, inclusive de outras sessões e de antes do limite
    do histórico recente.

    Os embeddings são gerados pelo ChromaDB no próprio processo (modelo all-MiniLM-L6-v2,
    baixado para ~/.cache/chroma no primeiro uso), então funciona com qualquer LLM.
    Tudo é best-effort: com o ChromaDB fora do ar, o agente segue sem lembranças.
    """

    # Com o ChromaDB fora do ar, espera esse tempo antes de tentar conectar de novo,
    # para não pagar uma tentativa de conexão a cada mensagem.
    RETRY_SECONDS = 60
    # Distância L2 (ao quadrado) máxima para uma lembrança contar como relevante. Com os
    # embeddings normalizados do modelo padrão, 1.1 equivale a similaridade de cosseno 0.45.
    # Medido em português: lembrança relevante ~0.97, sem relação ~1.24.
    MAX_DISTANCE = 1.1

    def __init__(self, collection_name: str = "mvp_long_term_memory"):
        self.collection_name = collection_name
        self._collection = None
        self._next_attempt = 0.0
        self._lock = threading.Lock()

    def _get_collection(self):
        """Conecta sob demanda: o import do chromadb é lento e o servidor pode subir depois."""
        if self._collection is not None:
            return self._collection
        if time.monotonic() < self._next_attempt:
            return None

        with self._lock:
            if self._collection is not None:
                return self._collection
            try:
                import chromadb
                from chromadb.config import Settings as ChromaSettings

                client = chromadb.HttpClient(
                    host=settings.CHROMADB_HOST,
                    port=settings.CHROMADB_PORT,
                    settings=ChromaSettings(anonymized_telemetry=False),
                )
                self._collection = client.get_or_create_collection(name=self.collection_name)
                logger.info("Conexão com ChromaDB (Vector Memory) estabelecida com sucesso.")
            except Exception as e:
                self._disconnect(f"Falha ao conectar no ChromaDB: {e}")
        return self._collection

    def _disconnect(self, reason: str):
        logger.warning(f"[VectorMemory] {reason}. Nova tentativa em {self.RETRY_SECONDS}s.")
        self._collection = None
        self._next_attempt = time.monotonic() + self.RETRY_SECONDS

    def remember_exchange(self, user_id: str, session_id: str, user_message: str, assistant_message: str):
        """Guarda uma troca completa como uma lembrança do usuário."""
        collection = self._get_collection()
        if collection is None:
            return

        try:
            collection.add(
                ids=[uuid.uuid4().hex],
                documents=[f"Usuário: {user_message}\nAssistente: {assistant_message}"],
                metadatas=[{
                    "user_id": user_id,
                    "session_id": session_id,
                    "created_at": datetime.utcnow().isoformat(timespec="seconds"),
                }],
            )
        except Exception as e:
            self._disconnect(f"Erro ao salvar lembrança no ChromaDB: {e}")

    def recall(self, user_id: str, query: str, top_k: int = 3) -> List[str]:
        """
        Devolve as lembranças do usuário mais parecidas com a mensagem. O filtro por
        user_id é o que impede o agente de contar a alguém a conversa de outra pessoa.
        """
        collection = self._get_collection()
        if collection is None or not query.strip():
            return []

        try:
            results = collection.query(
                query_texts=[query],
                n_results=top_k,
                where={"user_id": user_id},
                include=["documents", "distances", "metadatas"],
            )
        except Exception as e:
            self._disconnect(f"Erro ao buscar lembranças no ChromaDB: {e}")
            return []

        documents = (results.get("documents") or [[]])[0]
        distances = (results.get("distances") or [[]])[0]
        metadatas = (results.get("metadatas") or [[]])[0]

        memories = []
        for text, distance, metadata in zip(documents, distances, metadatas):
            if distance is not None and distance <= self.MAX_DISTANCE:
                memories.append(self._format(text, metadata))
        return memories

    @staticmethod
    def _format(text: str, metadata: Optional[dict]) -> str:
        created_at = (metadata or {}).get("created_at")
        return f"[{created_at}] {text}" if created_at else text

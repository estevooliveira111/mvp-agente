import math
from typing import List, Dict, Any
from models.memory import VectorDocument

class VectorMemory:
    """
    Gerencia a Memória de Longo Prazo da IA (RAG - Retrieval-Augmented Generation).
    Armazena e busca contextos antigos baseados em similaridade semântica.
    """
    def __init__(self):
        # Em um ambiente de produção, substituir por ChromaDB, Pinecone, FAISS ou Qdrant.
        # Para o MVP, usamos uma lista em memória para validar o RAG de forma simples.
        self.documents: List[VectorDocument] = []
        
    def add_document(self, doc_id: str, text: str, embedding: List[float], metadata: Dict[str, Any] = None):
        """Adiciona um novo conhecimento à memória da IA."""
        doc = VectorDocument(id=doc_id, text=text, embedding=embedding, metadata=metadata or {})
        self.documents.append(doc)
        
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Cálculo matemático puro de similaridade entre duas frases/vetores."""
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm_a = math.sqrt(sum(a * a for a in vec1))
        norm_b = math.sqrt(sum(b * b for b in vec2))
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
            
        return dot_product / (norm_a * norm_b)
        
    def search_similar(self, query_embedding: List[float], top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Busca as lembranças mais próximas da pergunta atual.
        Útil para a IA lembrar de coisas de 3 meses atrás.
        """
        if not self.documents:
            return []
            
        scored_docs = []
        for doc in self.documents:
            score = self._cosine_similarity(query_embedding, doc.embedding)
            scored_docs.append((score, doc))
            
        # Ordena do maior (mais similar) para o menor
        scored_docs.sort(key=lambda x: x[0], reverse=True)
        
        # Retorna apenas os top_k (ex: 3 melhores matches)
        results = []
        for score, doc in scored_docs[:top_k]:
            results.append({
                "score": round(score, 4),
                "text": doc.text,
                "metadata": doc.metadata
            })
            
        return results

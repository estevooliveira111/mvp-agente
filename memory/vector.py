from typing import List, Dict, Any
import chromadb
from models.memory import VectorDocument
from core.config import settings
from core.logger import logger

class VectorMemory:
    """
    Gerencia a Memória de Longo Prazo da IA (RAG) integrada fisicamente ao banco ChromaDB.
    """
    def __init__(self, collection_name: str = "mvp_knowledge_base"):
        try:
            # Conecta ao container ChromaDB externo
            self.client = chromadb.HttpClient(host=settings.CHROMADB_HOST, port=settings.CHROMADB_PORT)
            # Acessa a coleção ou a cria caso não exista
            self.collection = self.client.get_or_create_collection(name=collection_name)
            logger.info("Conexão com ChromaDB (Vector Memory) estabelecida com sucesso.")
        except Exception as e:
            logger.error(f"Falha ao conectar no ChromaDB: {e}")
            self.client = None
            self.collection = None
        
    def add_document(self, doc_id: str, text: str, embedding: List[float], metadata: Dict[str, Any] = None):
        """Adiciona um novo conhecimento ao banco vetorial."""
        if not self.collection:
            logger.warning("ChromaDB não está conectado. Documento não salvo.")
            return
            
        try:
            # ChromaDB fará a persistência física desses dados no container
            self.collection.add(
                ids=[doc_id],
                embeddings=[embedding],
                documents=[text],
                metadatas=[metadata or {}]
            )
        except Exception as e:
            logger.error(f"Erro ao adicionar documento no ChromaDB: {e}")
        
    def search_similar(self, query_embedding: List[float], top_k: int = 3) -> List[Dict[str, Any]]:
        """Busca as lembranças mais próximas no ChromaDB via similaridade semântica acelerada."""
        if not self.collection:
            return []
            
        try:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k
            )
            
            output = []
            if results and 'documents' in results and results['documents']:
                for i in range(len(results['documents'][0])):
                    output.append({
                        # O ChromaDB retorna distância. Na métrica padrão (L2), menor é mais similar.
                        "distance": results['distances'][0][i] if 'distances' in results else 0.0,
                        "text": results['documents'][0][i],
                        "metadata": results['metadatas'][0][i] if 'metadatas' in results else {}
                    })
            return output
            
        except Exception as e:
            logger.error(f"Erro ao buscar documentos similares no ChromaDB: {e}")
            return []

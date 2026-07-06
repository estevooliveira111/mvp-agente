import json
from typing import Any, Optional
from pymemcache.client.base import Client
from core.config import settings
from core.logger import logger

class CacheMemory:
    """
    Memória de Curtíssimo Prazo (Ultra-rápida) integrada fisicamente ao Memcached.
    Usada para fazer 'rate-limiting' do agente, cache de respostas frequentes, e locks distribuídos.
    """
    def __init__(self):
        try:
            self.client = Client((settings.MEMCACHED_HOST, settings.MEMCACHED_PORT))
            # Faz uma chamada leve para testar a conexão real com o container
            self.client.version()
            logger.info("Conexão com Memcached (Cache Memory) estabelecida com sucesso.")
        except Exception as e:
            logger.error(f"Falha ao conectar no Memcached: {e}")
            self.client = None
        
    def set(self, key: str, value: Any, ttl_seconds: int = 3600):
        """Salva um dado no Memcached com tempo de vida definido."""
        if not self.client:
            return
        try:
            # Serializa para JSON pois o Memcached lida com strings/bytes
            serialized = json.dumps(value)
            self.client.set(key, serialized, expire=ttl_seconds)
        except Exception as e:
            logger.error(f"Erro ao salvar chave '{key}' no Memcached: {e}")
        
    def get(self, key: str) -> Optional[Any]:
        """Recupera um dado do Memcached e o desserializa."""
        if not self.client:
            return None
        try:
            result = self.client.get(key)
            if result:
                return json.loads(result.decode('utf-8'))
        except Exception as e:
            logger.error(f"Erro ao ler chave '{key}' do Memcached: {e}")
        return None
        
    def delete(self, key: str):
        """Apaga a chave no Memcached."""
        if not self.client:
            return
        try:
            self.client.delete(key)
        except Exception as e:
            logger.error(f"Erro ao deletar chave '{key}' do Memcached: {e}")

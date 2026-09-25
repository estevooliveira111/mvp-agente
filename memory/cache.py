import json
from typing import Any, Optional
from pymemcache.client.base import Client
from core.config import settings
from core.logger import logger

class CacheMemory:
    """
    Memória de Curtíssimo Prazo (Ultra-rápida) integrada fisicamente ao Memcached.
    Usada para deduplicar os webhooks do Telegram e para guardar resultados de LLM que
    só dependem da mensagem (ex: a intenção detectada pelo IntentDetector).

    Tudo é best-effort: com o Memcached fora do ar, as leituras voltam vazias e quem
    chama segue sem cache. O pymemcache conecta sob demanda, então o servidor pode
    subir depois do agente.
    """
    def __init__(self):
        self.client = Client(
            (settings.MEMCACHED_HOST, settings.MEMCACHED_PORT),
            connect_timeout=1,
            timeout=1,
        )
        
    def set(self, key: str, value: Any, ttl_seconds: int = 3600):
        """Salva um dado no Memcached com tempo de vida definido."""
        try:
            # Serializa para JSON pois o Memcached lida com strings/bytes
            self.client.set(key, json.dumps(value), expire=ttl_seconds)
        except Exception as e:
            logger.warning(f"[CacheMemory] Erro ao salvar chave '{key}' no Memcached: {e}")

    def add(self, key: str, value: Any, ttl_seconds: int = 3600) -> Optional[bool]:
        """
        Salva só se a chave ainda não existir (operação atômica no Memcached).
        Devolve True se salvou, False se a chave já existia e None se o cache está fora do ar.
        """
        try:
            # noreply=False: sem a resposta do servidor, não dá para saber se a chave já existia.
            return bool(self.client.add(key, json.dumps(value), expire=ttl_seconds, noreply=False))
        except Exception as e:
            logger.warning(f"[CacheMemory] Erro ao adicionar chave '{key}' no Memcached: {e}")
            return None
        
    def get(self, key: str) -> Optional[Any]:
        """Recupera um dado do Memcached e o desserializa."""
        try:
            result = self.client.get(key)
            if result:
                return json.loads(result.decode('utf-8'))
        except Exception as e:
            logger.warning(f"[CacheMemory] Erro ao ler chave '{key}' do Memcached: {e}")
        return None
        
    def delete(self, key: str):
        """Apaga a chave no Memcached."""
        try:
            self.client.delete(key)
        except Exception as e:
            logger.warning(f"[CacheMemory] Erro ao deletar chave '{key}' do Memcached: {e}")

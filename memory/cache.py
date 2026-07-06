import time
from typing import Any, Optional
from models.memory import CacheEntry

class CacheMemory:
    """
    Memória de Curtíssimo Prazo (Ultra-rápida).
    Usada para armazenar tokens de API temporários, evitar processamento duplicado 
    ou fazer 'rate-limiting' do agente.
    """
    def __init__(self):
        # MVP: Dicionário. Produção: Redis/Memcached.
        self._store: dict[str, CacheEntry] = {}
        
    def set(self, key: str, value: Any, ttl_seconds: int = 3600):
        """Salva um dado com Time-To-Live (Tempo de vida) específico."""
        expires_at = time.time() + ttl_seconds
        self._store[key] = CacheEntry(key=key, value=value, expires_at=expires_at)
        
    def get(self, key: str) -> Optional[Any]:
        """Recupera um dado se ele ainda estiver válido."""
        if key in self._store:
            entry = self._store[key]
            if time.time() < entry.expires_at:
                return entry.value
            else:
                # O dado passou do prazo de validade (TTL), apaga-o.
                del self._store[key]
        return None
        
    def delete(self, key: str):
        """Apaga forçadamente um dado do cache."""
        if key in self._store:
            del self._store[key]
            
    def clear_expired(self):
        """Rotina de manutenção para limpar chaves vencidas."""
        now = time.time()
        expired_keys = [k for k, v in self._store.items() if now >= v.expires_at]
        for k in expired_keys:
            del self._store[k]

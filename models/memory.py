from dataclasses import dataclass, field
from typing import List, Dict, Any

@dataclass
class VectorDocument:
    """Representa um documento ou bloco de texto vetorizado para memória de longo prazo."""
    id: str
    text: str
    embedding: List[float]
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class CacheEntry:
    """Representa uma entrada de memória de altíssima velocidade (Cache/Redis)."""
    key: str
    value: Any
    expires_at: float

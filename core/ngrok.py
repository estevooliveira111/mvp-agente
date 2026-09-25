"""
Descoberta da URL pública do ngrok, para registrar o webhook do Telegram sem copiar
a URL à mão a cada vez que o túnel reinicia (no plano gratuito, ela muda sempre).

O ngrok expõe uma API local (por padrão em http://localhost:4040) que lista os túneis
abertos. Só é consultada quando WEBHOOK_URL está vazia.
"""
import time
from typing import Optional

import requests

from core.logger import logger


def _find_tunnel_url(tunnels: list, port: int) -> Optional[str]:
    """Escolhe o túnel HTTPS que aponta para a porta da API."""
    for tunnel in tunnels:
        addr = str(tunnel.get("config", {}).get("addr", ""))
        public_url = tunnel.get("public_url", "")
        if public_url.startswith("https://") and addr.rstrip("/").endswith(f":{port}"):
            return public_url
    return None


def discover_public_url(api_url: str, port: int, attempts: int = 10, delay_seconds: float = 1.0) -> Optional[str]:
    """
    Devolve a URL pública do túnel do ngrok para a porta informada, ou None se o ngrok
    não estiver rodando. Tenta algumas vezes porque, no 'make dev', o ngrok e a API sobem
    juntos e o túnel pode ainda não estar pronto.
    """
    for attempt in range(1, attempts + 1):
        try:
            response = requests.get(f"{api_url.rstrip('/')}/api/tunnels", timeout=2)
            response.raise_for_status()
            url = _find_tunnel_url(response.json().get("tunnels", []), port)
            if url:
                return url
        except (requests.RequestException, ValueError):
            pass
        if attempt < attempts:
            time.sleep(delay_seconds)

    logger.warning(f"[ngrok] Nenhum túnel HTTPS para a porta {port} encontrado em {api_url}.")
    return None

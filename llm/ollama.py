import json
import requests
from typing import List, Dict, Optional
from llm.base import BaseLLM
from core.logger import logger

class OllamaLLM(BaseLLM):
    """
    Integração Local via HTTP REST para o servidor Ollama (ex: Llama3, Mistral).
    Isso roda 100% offline, dependendo apenas do binário Ollama rodando no PC.
    """
    
    def __init__(self, model: str = "llama3", base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url
        
    def _build_messages(self, prompt: str, system_prompt: Optional[str], history: Optional[List[Dict[str, str]]]) -> list:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": prompt})
        return messages
        
    def generate_text(self, prompt: str, system_prompt: Optional[str] = None, history: Optional[List[Dict[str, str]]] = None) -> str:
        logger.info(f"[OllamaLLM] Enviando requisição local para o modelo {self.model}")
        try:
            payload = {
                "model": self.model,
                "messages": self._build_messages(prompt, system_prompt, history),
                "stream": False
            }
            # O timeout precisa ser maior para modelos locais que as vezes travam por GPU lenta
            response = requests.post(f"{self.base_url}/api/chat", json=payload, timeout=300)
            response.raise_for_status()
            
            data = response.json()
            if "message" in data:
                return data["message"].get("content", "")
            return str(data)
        except Exception as e:
            logger.error(f"[OllamaLLM] Falha na geração local via Ollama: {e}")
            return f"Erro de conexão com o servidor Ollama ({self.base_url}): {e}"
        
    def generate_json(self, prompt: str, system_prompt: Optional[str] = None) -> dict:
        logger.info(f"[OllamaLLM] Forçando JSON nativo na requisição Ollama ({self.model})")
        try:
            payload = {
                "model": self.model,
                "messages": self._build_messages(prompt, system_prompt, None),
                "stream": False,
                "format": "json" # O Ollama suporta nativamente 'JSON Mode' nesta diretiva!
            }
            response = requests.post(f"{self.base_url}/api/chat", json=payload, timeout=300)
            response.raise_for_status()
            
            content = response.json().get("message", {}).get("content", "{}")
            return json.loads(content)
        except json.JSONDecodeError as e:
            logger.error(f"[OllamaLLM] Falha ao tentar decodificar retorno local para JSON: {e}")
            return {"status": "error", "message": "O modelo não retornou um JSON válido."}
        except Exception as e:
            logger.error(f"[OllamaLLM] Falha crítica de conexão local: {e}")
            return {"status": "error", "message": str(e)}

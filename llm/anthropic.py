import os
import json
from typing import List, Dict, Optional
from llm.base import BaseLLM
from core.logger import logger
import anthropic

class AnthropicLLM(BaseLLM):
    """
    Integração real com a API da Anthropic (Claude 3).
    Utiliza o SDK oficial `anthropic`.
    """
    
    def __init__(self, model: str = "claude-3-opus-20240229"):
        self.model = model
        self.api_key = os.getenv("ANTHROPIC_API_KEY", "")
        self.client = anthropic.Anthropic(api_key=self.api_key)
        
    def _build_messages(self, prompt: str, history: Optional[List[Dict[str, str]]]) -> list:
        """Claude Messages API espera apenas user/assistant. System prompt vai à parte."""
        messages = []
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": prompt})
        return messages
        
    def generate_text(self, prompt: str, system_prompt: Optional[str] = None, history: Optional[List[Dict[str, str]]] = None) -> str:
        logger.info(f"[AnthropicLLM] Gerando texto via API com {self.model}")
        try:
            kwargs = {
                "model": self.model,
                "max_tokens": 4096,
                "messages": self._build_messages(prompt, history)
            }
            if system_prompt:
                # O System Prompt no Claude entra como parâmetro global da API e não no array de messages
                kwargs["system"] = system_prompt
                
            response = self.client.messages.create(**kwargs)
            return response.content[0].text
        except Exception as e:
            logger.error(f"[AnthropicLLM] Falha na geração de texto: {e}")
            return f"Erro na comunicação com a Anthropic: {e}"
        
    def generate_json(self, prompt: str, system_prompt: Optional[str] = None) -> dict:
        logger.info(f"[AnthropicLLM] Forçando output JSON por System Prompt com {self.model}")
        try:
            # O Claude não possui um 'json_object' type oficial, então forçamos firmemente via prompt
            sys_prompt = system_prompt or "Você é uma IA analítica."
            sys_prompt += "\n\nCRÍTICO: Sua resposta DEVE ser estritamente um JSON válido e puro. Sem Markdown, sem explicações, sem crases de código. Inicie com { e termine com }."
            
            kwargs = {
                "model": self.model,
                "max_tokens": 4096,
                "system": sys_prompt,
                "messages": [{"role": "user", "content": prompt}]
            }
            
            response = self.client.messages.create(**kwargs)
            raw_text = response.content[0].text.strip()
            
            # Limpeza preventiva caso o Claude coloque marcações Markdown teimosas
            if raw_text.startswith("```json"):
                raw_text = raw_text[7:]
            if raw_text.startswith("```"):
                raw_text = raw_text[3:]
            if raw_text.endswith("```"):
                raw_text = raw_text[:-3]
                
            return json.loads(raw_text.strip())
        except json.JSONDecodeError as e:
            logger.error(f"[AnthropicLLM] Falha ao parsear a resposta como JSON: {e}")
            return {"status": "error", "message": "O Claude inseriu lixo textual em volta do JSON.", "raw": raw_text}
        except Exception as e:
            logger.error(f"[AnthropicLLM] Falha na requisição API: {e}")
            return {"status": "error", "message": str(e)}

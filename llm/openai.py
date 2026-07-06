import os
import json
from typing import List, Dict, Optional
from llm.base import BaseLLM
from core.logger import logger
import openai

class OpenAILLM(BaseLLM):
    """
    Integração real com a API da OpenAI.
    Utiliza o SDK oficial `openai`.
    """
    
    def __init__(self, model: str = "gpt-4o"):
        self.model = model
        self.api_key = os.getenv("OPENAI_API_KEY", "")
        self.client = openai.OpenAI(api_key=self.api_key)
        
    def _build_messages(self, prompt: str, system_prompt: Optional[str], history: Optional[List[Dict[str, str]]]) -> list:
        """Utilitário para montar a estrutura de histórico padrão do Chat Completions."""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": prompt})
        return messages
        
    def generate_text(self, prompt: str, system_prompt: Optional[str] = None, history: Optional[List[Dict[str, str]]] = None) -> str:
        logger.info(f"[OpenAILLM] Gerando texto via API com modelo {self.model}")
        try:
            messages = self._build_messages(prompt, system_prompt, history)
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"[OpenAILLM] Falha na geração de texto: {e}")
            return f"Erro na comunicação com a OpenAI: {e}"
        
    def generate_json(self, prompt: str, system_prompt: Optional[str] = None) -> dict:
        logger.info(f"[OpenAILLM] Gerando JSON estruturado (response_format='json_object') com {self.model}")
        try:
            # Dica da documentação: para forçar JSON, a palavra 'json' precisa existir no system prompt
            sys_prompt = system_prompt or "Você é um bot de API."
            if "json" not in sys_prompt.lower():
                sys_prompt += " Retorne sua resposta estritamente em formato JSON."
                
            messages = self._build_messages(prompt, sys_prompt, None)
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                response_format={"type": "json_object"}
            )
            content = response.choices[0].message.content
            return json.loads(content)
        except json.JSONDecodeError as e:
            logger.error(f"[OpenAILLM] Falha ao decodificar JSON da OpenAI: {e}")
            return {"status": "error", "message": "O modelo não retornou um JSON válido."}
        except Exception as e:
            logger.error(f"[OpenAILLM] Falha crítica na API: {e}")
            return {"status": "error", "message": str(e)}

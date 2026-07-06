import os
import json
from typing import List, Dict, Optional
from llm.base import BaseLLM
from core.logger import logger
import google.generativeai as genai

class GeminiLLM(BaseLLM):
    """
    Integração oficial com a API do Google Gemini (Família Gemini 1.5 Pro / Flash).
    Utiliza o SDK oficial `google-generativeai`.
    """
    
    def __init__(self, model: str = "gemini-2.5-flash"):
        self.model = model
        self.api_key = os.getenv("GEMINI_API_KEY", "")
        if self.api_key:
            genai.configure(api_key=self.api_key)
        else:
            logger.warning("[GeminiLLM] GEMINI_API_KEY não encontrada no ambiente (.env).")
        
    def _build_messages(self, prompt: str, history: Optional[List[Dict[str, str]]]) -> list:
        """
        O Gemini usa a nomenclatura 'user' e 'model' para histórico.
        Como nosso padrão interno usa 'user' e 'assistant', fazemos a conversão aqui.
        """
        messages = []
        if history:
            for msg in history:
                role = "model" if msg["role"] == "assistant" else "user"
                messages.append({"role": role, "parts": [msg["content"]]})
        messages.append({"role": "user", "parts": [prompt]})
        return messages

    def generate_text(self, prompt: str, system_prompt: Optional[str] = None, history: Optional[List[Dict[str, str]]] = None) -> str:
        logger.info(f"[GeminiLLM] Gerando texto via API com modelo {self.model}")
        try:
            model_instance = genai.GenerativeModel(
                model_name=self.model,
                system_instruction=system_prompt if system_prompt else None
            )
            
            contents = self._build_messages(prompt, history)
            response = model_instance.generate_content(contents)
            return response.text
        except Exception as e:
            logger.error(f"[GeminiLLM] Falha na geração de texto: {e}")
            return f"Erro na comunicação com o Gemini: {e}"
        
    def generate_json(self, prompt: str, system_prompt: Optional[str] = None) -> dict:
        logger.info(f"[GeminiLLM] Forçando geração de JSON (application/json) no {self.model}")
        try:
            sys_prompt = system_prompt or "Você é um bot analítico e objetivo."
            
            model_instance = genai.GenerativeModel(
                model_name=self.model,
                system_instruction=sys_prompt
            )
            
            contents = self._build_messages(prompt, None)
            
            # O Gemini 1.5 tem suporte nativo a forçar a saída como JSON válido
            response = model_instance.generate_content(
                contents,
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json"
                )
            )
            
            return json.loads(response.text)
        except json.JSONDecodeError as e:
            logger.error(f"[GeminiLLM] Falha ao parsear JSON retornado: {e}")
            return {"status": "error", "message": "O Gemini não retornou um JSON válido.", "raw": response.text}
        except Exception as e:
            logger.error(f"[GeminiLLM] Falha na requisição API do Gemini: {e}")
            return {"status": "error", "message": str(e)}

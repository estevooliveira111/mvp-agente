import os
import json
from typing import List, Dict, Optional
from llm.base import BaseLLM
from core.exceptions import LLMException
from core.logger import logger
import anthropic

# Em recusa por segurança, a API refaz a chamada no modelo que a Anthropic recomenda
# para aquela categoria, em vez de devolver a recusa.
FALLBACK_BETA = "server-side-fallback-2026-07-01"


class AnthropicLLM(BaseLLM):
    """
    Integração real com a API da Anthropic (Claude).
    Utiliza o SDK oficial `anthropic`.
    """
    
    def __init__(self, model: str = "claude-opus-5"):
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

    def _create(self, messages: list, system_prompt: Optional[str]) -> str:
        """Chama a API e devolve só o texto (a resposta pode trazer blocos de thinking antes)."""
        kwargs = {
            "model": self.model,
            "max_tokens": 16000,
            "messages": messages,
            "betas": [FALLBACK_BETA],
            "fallbacks": "default",
        }
        if system_prompt:
            # O System Prompt no Claude entra como parâmetro global da API e não no array de messages
            kwargs["system"] = system_prompt

        try:
            response = self.client.beta.messages.create(**kwargs)
        except anthropic.APIError as e:
            raise LLMException(f"Falha na comunicação com a Anthropic: {e}") from e

        # Mesmo com fallback, toda a cadeia pode recusar.
        if response.stop_reason == "refusal":
            raise LLMException("O Claude recusou a solicitação.")

        text = "".join(block.text for block in response.content if block.type == "text")
        if not text:
            raise LLMException(f"O Claude não devolveu texto (stop_reason: {response.stop_reason}).")
        return text
        
    def generate_text(self, prompt: str, system_prompt: Optional[str] = None, history: Optional[List[Dict[str, str]]] = None) -> str:
        logger.info(f"[AnthropicLLM] Gerando texto via API com {self.model}")
        return self._create(self._build_messages(prompt, history), system_prompt)
        
    def generate_json(self, prompt: str, system_prompt: Optional[str] = None) -> dict:
        logger.info(f"[AnthropicLLM] Forçando output JSON por System Prompt com {self.model}")
        sys_prompt = system_prompt or "Você é uma IA analítica."
        sys_prompt += "\n\nSua resposta deve ser apenas um objeto JSON válido, sem Markdown nem texto em volta."

        raw_text = self._create([{"role": "user", "content": prompt}], sys_prompt).strip()

        # Limpeza preventiva caso o Claude coloque marcações Markdown
        if raw_text.startswith("```json"):
            raw_text = raw_text[7:]
        if raw_text.startswith("```"):
            raw_text = raw_text[3:]
        if raw_text.endswith("```"):
            raw_text = raw_text[:-3]

        try:
            return json.loads(raw_text.strip())
        except json.JSONDecodeError as e:
            logger.error(f"[AnthropicLLM] Falha ao parsear a resposta como JSON: {e}")
            raise LLMException("O Claude não devolveu um JSON válido.") from e

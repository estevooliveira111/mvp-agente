import os
from core.logger import logger
from llm.base import BaseLLM

def get_active_llm() -> BaseLLM:
    """
    Design Pattern: Factory.
    Verifica dinamicamente as chaves de API disponíveis no ambiente (.env) 
    e retorna a instância do provedor LLM correspondente.
    A ordem de prioridade define qual LLM assume se houver mais de uma chave.
    """
    
    # 1. Prioridade: OpenAI (GPT)
    if os.getenv("OPENAI_API_KEY") and os.getenv("OPENAI_API_KEY").startswith("sk-"):
        logger.info("[LLM Factory] Detectada chave válida da OpenAI. Inicializando GPT.")
        from llm.openai import OpenAILLM
        return OpenAILLM()
        
    # 2. Prioridade: Anthropic (Claude)
    if os.getenv("ANTHROPIC_API_KEY"):
        logger.info("[LLM Factory] Detectada chave da Anthropic. Inicializando Claude.")
        from llm.anthropic import AnthropicLLM
        return AnthropicLLM()
        
    # 3. Prioridade: Google Gemini
    if os.getenv("GEMINI_API_KEY"):
        logger.info("[LLM Factory] Detectada chave do Gemini. Inicializando Gemini 1.5.")
        from llm.gemini import GeminiLLM
        return GeminiLLM()
        
    # 4. Fallback: Ollama Local (Localhost - Sem custos/chaves)
    logger.warning("[LLM Factory] ⚠️ Nenhuma chave de API de Nuvem encontrada no arquivo .env!")
    logger.warning("[LLM Factory] Realizando fallback de emergência para motor open-source local (Ollama).")
    logger.warning("Certifique-se que o serviço Ollama está rodando na porta 11434.")
    from llm.ollama import OllamaLLM
    return OllamaLLM()

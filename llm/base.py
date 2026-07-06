from abc import ABC, abstractmethod
from typing import List, Dict, Optional

class BaseLLM(ABC):
    """
    Interface base que dita o contrato para qualquer provedor de Inteligência Artificial.
    Isso aplica o Design Pattern 'Strategy', permitindo que o Agente troque 
    a OpenAI pelo Ollama (local) mudando apenas uma linha no arquivo principal, 
    sem quebrar nenhuma lógica de negócios.
    """
    
    @abstractmethod
    def generate_text(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None, 
        history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """
        Gera uma resposta em formato de texto livre.
        Padrão utilizado pelo Manager Agent para falar com o usuário.
        """
        pass
        
    @abstractmethod
    def generate_json(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None
    ) -> dict:
        """
        Gera uma resposta estritamente estruturada e tipada em JSON.
        Padrão utilizado pelo Planner Agent para acionar ferramentas com segurança.
        """
        pass

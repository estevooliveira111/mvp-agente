from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class ToolDefinition:
    """Define a assinatura e os metadados de uma ferramenta que a IA pode usar."""
    name: str
    description: str
    parameters: Dict[str, Any]

@dataclass
class ToolExecutionRequest:
    """Representa o pedido da IA para executar uma ferramenta específica."""
    tool_name: str
    arguments: Dict[str, Any]
    execution_id: str
    
@dataclass
class ToolExecutionResult:
    """Representa o resultado devolvido por uma ferramenta após a execução."""
    execution_id: str
    tool_name: str
    status: str # 'success', 'error'
    data: Any
    error_message: str = ""

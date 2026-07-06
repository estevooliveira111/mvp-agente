import os
import importlib
from core.logger import logger

def load_all_tools():
    """
    Varre o diretório 'tools/' automaticamente (Auto-Discovery).
    Identifica arquivos Python que possuam a função 'execute' e a constante 'tool_metadata'.
    
    Retorna uma tupla:
    - registry: dict com { "nome_do_arquivo": funcao_execute } (para o Executor Agent)
    - metadata_list: list com todos os JSONs de metadados (para o Planner Agent saber o que usar)
    """
    registry = {}
    metadata_list = []
    
    tools_dir = os.path.dirname(__file__)
    
    for filename in os.listdir(tools_dir):
        if filename.endswith(".py") and filename not in ["__init__.py", "registry.py"]:
            module_name = filename[:-3] # Remove '.py'
            try:
                # Importa o arquivo da ferramenta dinamicamente
                module = importlib.import_module(f"tools.{module_name}")
                
                # Checa se o contrato da ferramenta existe (execute + tool_metadata)
                if hasattr(module, "execute") and hasattr(module, "tool_metadata"):
                    registry[module_name] = module.execute
                    metadata_list.append(module.tool_metadata)
                    logger.debug(f"[Tools Registry] Ferramenta '{module_name}' carregada com sucesso.")
            except Exception as e:
                logger.error(f"[Tools Registry] Falha ao carregar ferramenta '{module_name}': {e}")
                
    logger.info(f"[Tools Registry] Total de {len(registry)} ferramentas carregadas e armadas.")
    return registry, metadata_list

import json
import os
from core.config import settings

# Pasta raiz do projeto (tools/..). Caminhos relativos em FILE_READ_BASE_DIR partem daqui.
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 1. Metadados: Define como a IA enxerga esta ferramenta
tool_metadata = {
    "name": "file_read",
    "description": "Lê o conteúdo de arquivos de texto da pasta de arquivos do agente (ex: datasets, anotações). Não acessa nada fora dessa pasta.",
    "parameters": {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "O caminho do arquivo, relativo à pasta de arquivos do agente (ex: 'relatorio.txt', 'dados/vendas.csv')."
            }
        },
        "required": ["file_path"]
    }
}

# 2. Execução: O que roda quando a IA chama a ferramenta
def execute(**kwargs):
    """
    Lê um arquivo local e retorna seu conteúdo como texto.
    """
    file_path = kwargs.get("file_path")
    
    if not file_path:
        return json.dumps({"status": "error", "message": "O parâmetro 'file_path' é obrigatório."})
        
    try:
        # Só lê dentro de FILE_READ_BASE_DIR. O realpath resolve '..' e links simbólicos
        # antes da checagem; sem isso, a IA (ou quem conversa com ela) leria o .env com
        # as chaves de API e o JWT_SECRET_KEY.
        base_dir = os.path.realpath(os.path.join(PROJECT_ROOT, settings.FILE_READ_BASE_DIR))
        target_path = os.path.realpath(os.path.join(base_dir, file_path))

        if os.path.commonpath([base_dir, target_path]) != base_dir:
            return json.dumps({"status": "error", "message": f"Acesso negado: '{file_path}' está fora da pasta de arquivos do agente."})

        if not os.path.exists(target_path):
            return json.dumps({"status": "error", "message": f"O arquivo '{file_path}' não foi encontrado."})
            
        if not os.path.isfile(target_path):
            return json.dumps({"status": "error", "message": f"O caminho '{file_path}' não aponta para um arquivo válido (pode ser um diretório)."})
            
        # Lê o arquivo
        with open(target_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Segurança: se o arquivo for gigantesco (ex: um log gigante ou dataset enorme),
        # truncamos para evitar estourar o limite de tokens da IA (context window).
        max_chars = 15000
        if len(content) > max_chars:
            content = content[:max_chars] + f"\n\n... [Aviso: Conteúdo truncado. O arquivo possui {len(content)} caracteres, mostrando apenas os primeiros {max_chars}]."
            
        return json.dumps({
            "status": "success",
            "data": content
        })
        
    except UnicodeDecodeError:
        return json.dumps({
            "status": "error",
            "message": f"O arquivo '{file_path}' parece ser binário ou usar uma codificação não suportada (diferente de UTF-8)."
        })
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"Erro ao tentar ler o arquivo '{file_path}': {str(e)}"
        })

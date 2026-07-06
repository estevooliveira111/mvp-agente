import json
import os

# 1. Metadados: Define como a IA enxerga esta ferramenta
tool_metadata = {
    "name": "file_read",
    "description": "Lê o conteúdo de arquivos locais do projeto. Uso: análise de configs, logs, datasets ou qualquer outro arquivo de texto.",
    "parameters": {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "O caminho (relativo ou absoluto) do arquivo que deve ser lido (ex: 'config.json', 'logs/app.log')."
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
        # Resolve o caminho para absoluto, garantindo que seja relativo à pasta onde o script está rodando
        target_path = os.path.abspath(file_path)
        
        if not os.path.exists(target_path):
            return json.dumps({"status": "error", "message": f"O arquivo '{file_path}' não foi encontrado."})
            
        if not os.path.isfile(target_path):
            return json.dumps({"status": "error", "message": f"O caminho '{file_path}' não aponta para um arquivo válido (pode ser um diretório)."})
            
        # Lê o arquivo
        with open(target_path, 'r', encoding='utf-8') as f:
            conteudo = f.read()
            
        # Segurança: se o arquivo for gigantesco (ex: um log gigante ou dataset enorme),
        # truncamos para evitar estourar o limite de tokens da IA (context window).
        max_chars = 15000
        if len(conteudo) > max_chars:
            conteudo = conteudo[:max_chars] + f"\n\n... [Aviso: Conteúdo truncado. O arquivo possui {len(conteudo)} caracteres, mostrando apenas os primeiros {max_chars}]."
            
        return json.dumps({
            "status": "success",
            "data": conteudo
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

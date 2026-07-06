# Planejamento de Ferramentas (Tools)

Este diretório armazenará todas as ferramentas (tools) que o chat da IA poderá utilizar. Para que o agente consiga identificar, ler os parâmetros e executar a ferramenta corretamente, **cada arquivo deve seguir um padrão específico.**

## Estrutura Padrão

Todas as ferramentas devem ser escritas em **Python** (com base nas dependências do projeto) e devem expor obrigatoriamente duas coisas:

1. **`tool_metadata` (Metadados)**: Define o nome, a descrição e os parâmetros que a IA precisa preencher.
2. **`execute` (Função de Execução)**: A função que o código principal vai chamar quando a IA decidir usar a ferramenta.

---

## Template de Exemplo (`exemplo_ferramenta.py`)

Abaixo está o código base que todo novo arquivo dentro da pasta `tools/` deve ter:

```python
import json

# 1. Metadados: Define como a IA enxerga esta ferramenta
tool_metadata = {
    "name": "nome_da_ferramenta",
    "description": "Descreva aqui, de forma clara, o que a ferramenta faz e em que cenário o LLM deve chamá-la.",
    "parameters": {
        "type": "object",
        "properties": {
            "parametro_exemplo": {
                "type": "string",
                "description": "Descrição clara sobre o que é este parâmetro."
            },
            "outro_parametro": {
                "type": "integer",
                "description": "Descrição deste número."
            }
        },
        "required": ["parametro_exemplo"] # Lista de parâmetros obrigatórios
    }
}

# 2. Execução: O que roda quando a IA chama a ferramenta
def execute(**kwargs):
    """
    Função principal executada pelo sistema.
    O dicionário kwargs conterá os argumentos enviados pela IA.
    """
    # Captura os argumentos recebidos da IA
    param_ex = kwargs.get("parametro_exemplo")
    outro_param = kwargs.get("outro_parametro", 0)
    
    try:
        # ==========================================
        # COLOQUE A LÓGICA DA SUA FERRAMENTA AQUI
        # ==========================================
        
        resultado = f"Processado: {param_ex} com valor {outro_param}."
        
        # É recomendado sempre retornar uma string (ou JSON stringificado)
        # para que a IA consiga ler facilmente a resposta da ferramenta.
        return json.dumps({
            "status": "success",
            "data": resultado
        })
        
    except Exception as e:
        # Se falhar, informe o erro de volta para a IA entender o que houve
        return json.dumps({
            "status": "error",
            "message": str(e)
        })
```

## Como o Sistema Vai Funcionar

1. **Descoberta**: O arquivo principal (ex: `app.py` ou `main.py`) vai varrer a pasta `tools/`.
2. **Registro**: Para cada arquivo `.py` encontrado, ele importa o `tool_metadata` e o adiciona à lista de ferramentas (tools) da IA (ex: usando a biblioteca `google-generativeai`).
3. **Execução**: Se, durante a conversa, a IA responder que precisa executar a ferramenta `nome_da_ferramenta`, o script principal pegará os argumentos que a IA gerou e os passará para a função `execute(**argumentos)` daquele arquivo.
4. **Retorno**: A resposta do `execute` será enviada de volta como uma mensagem de ferramenta para a IA continuar o raciocínio.

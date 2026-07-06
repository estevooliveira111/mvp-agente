# Ferramenta: `file_read`

## Descrição
Lê o conteúdo de arquivos locais do projeto. Uso: análise de configs, logs, datasets ou qualquer outro arquivo de texto.

## Parâmetros

| Nome | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `file_path` | `string` | ✅ Sim | O caminho (relativo ou absoluto) do arquivo que deve ser lido (ex: 'config.json', 'logs/app.log'). |

## Como Funciona Internamente
```text
Lê um arquivo local e retorna seu conteúdo como texto.
```

---
*Arquivo fonte: `tools/file_read.py`*
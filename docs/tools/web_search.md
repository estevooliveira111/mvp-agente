# Ferramenta: `web_search`

## Descrição
Busca informações externas na web. Uso: qualquer pergunta fora do conhecimento interno.

## Parâmetros

| Nome | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `query` | `string` | ✅ Sim | O termo, frase ou pergunta a ser pesquisada na web. |

## Como Funciona Internamente
```text
Realiza uma busca na web e retorna uma lista estruturada de resultados.
```

---
*Arquivo fonte: `tools/web_search.py`*
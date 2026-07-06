# Ferramenta: `prompt_builder`

## Descrição
Gera prompts altamente estruturados e otimizados para orientar outras IAs. Ideal para uso em um pipeline de agentes.

## Parâmetros

| Nome | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `task` | `string` | ✅ Sim | A tarefa principal que a outra IA deve executar (ex: 'Extrair entidades deste texto', 'Gerar um roteiro'). |
| `context` | `string` | ❌ Não | Contexto adicional, regras de negócio ou dados brutos necessários para a tarefa. |
| `output_format` | `string` | ❌ Não | O formato de saída desejado da IA (ex: 'JSON com os campos X e Y', 'Markdown formatado', 'Tabela'). |
| `persona` | `string` | ❌ Não | O tom, cargo ou a persona que a IA deve assumir (ex: 'Engenheiro de Software Sênior', 'Professor didático'). |

## Como Funciona Internamente
```text
Recebe pedaços lógicos de intenção e constrói um prompt profissional, 
    utilizando boas práticas de engenharia de prompt (seções, delimitadores, etc).
```

---
*Arquivo fonte: `tools/prompt_builder.py`*
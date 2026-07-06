# Ferramenta: `google_calendar_manager`

## Descrição
Ferramenta para criar eventos no Google Agenda (Calendar). Utiliza OAuth2 para autenticar usuários reais e injetar compromissos com horário e participantes na agenda.

## Parâmetros

| Nome | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `summary` | `string` | ✅ Sim | O título ou resumo do evento (ex: 'Reunião de Alinhamento do MVP'). |
| `description` | `string` | ❌ Não | Detalhes, laudos ou pauta sobre o evento. |
| `start_time` | `string` | ✅ Sim | Data e hora de início no formato ISO-8601. Exemplo: '2026-07-10T14:00:00-03:00' (para horário de Brasília). |
| `end_time` | `string` | ✅ Sim | Data e hora de fim no formato ISO-8601. Exemplo: '2026-07-10T15:00:00-03:00'. |
| `attendees` | `array` | ❌ Não | (Opcional) Lista de strings contendo os e-mails dos participantes a serem convidados. |

## Como Funciona Internamente
```text
1. Verifica se já existe um token de acesso de usuário (OAuth2).
    2. Se o token expirou, atualiza. Se não existe, pede login interativo e gera o token.
    3. Conecta com a Google Calendar API (v3).
    4. Constrói o JSON do evento estruturado e realiza o POST (insert).
```

---
*Arquivo fonte: `tools/google_calendar_manager.py`*
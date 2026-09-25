# Ferramenta: `telegram_sender`

## Descrição
Envia notificações e mensagens formatadas em tempo real usando a API HTTP oficial do Telegram Bot.

## Destinatários permitidos
Só envia para os chat_ids ou @usernames listados em `TELEGRAM_ALLOWED_CHAT_IDS` no `.env`. Com a lista vazia, todo envio é recusado: qualquer pessoa que fala com o bot pode pedir um envio.

## Parâmetros

| Nome | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `chat_id` | `string` | ✅ Sim | O ID (ou @username de canal) do chat ou usuário destino no Telegram. |
| `text` | `string` | ✅ Sim | O texto da mensagem a ser enviada. |
| `parse_mode` | `string` | ❌ Não | (Opcional) Formato de estilo do texto, geralmente 'Markdown' (padrão) ou 'HTML'. |

## Como Funciona Internamente
```text
Recebe um destinatário e envia a mensagem realizando um POST HTTP
    contra o endpoint do Telegram Bot, usando a biblioteca 'requests'.
```

---
*Arquivo fonte: `tools/telegram_sender.py`*
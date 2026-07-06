# Ferramenta: `email_sender`

## Descrição
Envia e-mails automatizados usando o protocolo SMTP com estruturação MIME. Permite envio de relatórios e mensagens em texto ou HTML, com opção de criptografar o conteúdo antes de enviar.

## Parâmetros

| Nome | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `to_email` | `string` | ✅ Sim | Endereço de e-mail de destino. |
| `subject` | `string` | ✅ Sim | Assunto do e-mail. |
| `body` | `string` | ✅ Sim | Corpo da mensagem (texto simples ou HTML). |
| `is_html` | `boolean` | ❌ Não | (Opcional) Define se a mensagem deve ser interpretada como HTML. O padrão é texto simples (false). |
| `encrypt_body` | `boolean` | ❌ Não | (Opcional) Se verdadeiro, o corpo da mensagem será cifrado com Fernet, garantindo confidencialidade absoluta em trânsito. |

## Como Funciona Internamente
```text
Constrói e envia um e-mail de forma segura usando smtplib.
    Autentica via TLS no servidor definido nas variáveis de ambiente.
```

---
*Arquivo fonte: `tools/email_sender.py`*
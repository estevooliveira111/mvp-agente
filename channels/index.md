# Arquitetura do Módulo de Canais (Channels)

O objetivo deste documento é definir a arquitetura base e os padrões de projeto do módulo de canais de comunicação. Este diretório será responsável por acoplar o núcleo inteligente da IA (AI Core) com o mundo exterior.

O módulo atua como uma **Camada de Abstração (Gateway)** unificada para plataformas diversas, tais como WhatsApp, Telegram, Discord, Slack, E-mail, Web Chat, SMS e outras APIs personalizadas.

⚠️ **IMPORTANTE:** Nenhuma regra de negócio, tomada de decisão ou lógica da inteligência artificial deve existir dentro deste diretório. A missão de um canal é estritamente **traduzir e rotear** a comunicação.

---

## 1. Responsabilidades de um Canal

Todo canal implementado dentro deste módulo deve seguir duas vias obrigatórias:

1. **Inbound (Entrada / Escuta)**
   - Conectar-se à plataforma externa (seja via Webhooks recebendo POSTs, Polling ativo ou WebSockets).
   - Extrair a mensagem em seu formato nativo.
   - Converter os dados brutos nativos para o **Payload Normalizado** do sistema.
   - Entregar o evento mastigado e padronizado para o núcleo da IA.

2. **Outbound (Saída / Envio)**
   - Receber a intenção de resposta gerada pela IA (no formato agnóstico do sistema).
   - Traduzir a intenção e seus eventuais botões, imagens e formatações (ex: Markdown universal) para o formato específico aceito pela API da plataforma de destino.
   - Disparar a requisição HTTP/WS de envio.

---

## 2. Padrão de Interface (Contrato do Canal)

Para garantir que a IA consiga se plugar facilmente a qualquer novo canal (Plug-and-Play), todo arquivo de integração (ex: `whatsapp.py`, `telegram.py`) deve expor, de preferência em uma classe ou funções encapsuladas, a seguinte estrutura base:

- `initialize()`: Carrega variáveis de ambiente e configura clientes/conexões da plataforma.
- `start_listener(callback)`: Função responsável por escutar eventos. O `callback` é o gatilho repassado pelo núcleo da IA que deverá ser chamado sempre que o usuário mandar uma mensagem.
- `send_message(recipient_id, standardized_payload)`: Função acionada pelo Core da IA sempre que precisar responder o usuário.

---

## 3. Payload Normalizado (Universal)

O segredo para um sistema multi-canal escalável é a normalização de dados. O núcleo da IA **não deve saber** se a mensagem veio do Slack ou do WhatsApp. Ele recebe um único formato universal.

Todo canal **deve converter** mensagens de Inbound para a estrutura abaixo antes de mandar para o Core:

```json
{
  "channel_type": "whatsapp",          // A identificação da plataforma
  "message_id": "wamid.123abc456",     // ID único na plataforma originária
  "user_id": "5511999999999",          // Identificador único do usuário (Telefone, Email, UUID)
  "user_metadata": {
    "name": "João da Silva",           // (Opcional) Nome no perfil
    "username": "@joaodasilva"         // (Opcional) Username se houver
  },
  "content": {
    "text": "Preciso de ajuda com meu pedido.",
    "attachments": [                   // (Opcional) Mídias anexadas na mensagem
      {
        "type": "image",               // image, audio, document, video
        "mime_type": "image/jpeg",
        "url_or_path": "https://..."
      }
    ]
  },
  "timestamp": "2026-07-06T15:00:00Z"
}
```

---

## 4. Estrutura Recomendada do Diretório

À medida que o projeto evoluir, o diretório seguirá a seguinte hierarquia organizacional:

```text
channels/
├── index.md                 # Esta documentação base da arquitetura
├── core_interface.py        # (A ser criado) A Interface ou BaseClass obrigatória
├── telegram/                # Integração isolada do Telegram
│   ├── listener.py
│   └── sender.py
├── whatsapp/                # Integração isolada da API Oficial/Cloud do WhatsApp
│   ├── webhook.py
│   └── sender.py
└── email/                   # Integração IMAP/SMTP
    └── ...
```

*(Nota: Para canais muito simples, a implementação pode residir em um único arquivo `.py` na raiz da pasta `channels/`)*

---

## 5. Políticas e Diretrizes de Engenharia

- **Segurança de Credenciais:** Absolutamente **nenhum** Token de Bot, Senha SMTP ou Chave de API de plataforma externa deve ser codificado (hardcoded) nos arquivos. O uso do pacote `python-dotenv` lendo o `.env` é terminantemente obrigatório.
- **Isolamento de Falhas:** Se o WhatsApp cair, o Telegram deve continuar funcionando. Os canais devem tratar exceções de rede e HTTP isoladamente (ex: try/except em requisições via `requests`) e passar o status do erro (ex: *Rate Limit*, *Unauthorized*) pro logger do sistema, **sem** derrubar (crash) o serviço do Agente.
- **Tratamento de Rate Limit:** A plataforma destino recusou a saída por "Too Many Requests"? O canal de outbound tem o dever de prever filas (Queues) ou *Exponential Backoffs* caso seja uma política da plataforma.

# MVP Agente

Orquestrador multi-agentes em Python, que atende pelo Telegram, pelo Discord, pelo terminal (CLI) e por uma API REST de chat, integrando histórico de conversa persistido, banco relacional e um catálogo de ferramentas (busca, e-mail, forense de imagem/áudio).

Este é um MVP em desenvolvimento ativo: a arquitetura segue padrões conhecidos (Strategy para os LLMs, injeção de dependências entre agentes, registry com auto-discovery de tools). Já existe uma suíte de testes automatizada (pytest + SQLite em memória, veja `tests/`) e autenticação JWT nas rotas REST, mas ainda não há hardening completo de produção — trate como base sólida para evoluir.

---

## 🏗 Arquitetura do Projeto

O sistema é modular, aplicando alguns padrões de Engenharia de Software (injeção de dependências, Strategy):

- **`agents/`**: Padrão _Multi-Agent_ simples, onde:
  - **Manager**: Conversa com o usuário e orquestra o fluxo.
  - **Planner**: Recebe o objetivo e o catálogo de tools, e desenha um plano de ação (JSON/Pipeline).
  - **Executor**: Executa as funções Python indicadas no plano.
- **`channels/`**: Bot do Discord. O webhook do Telegram e a API REST ficam em `app.py` e `api/routes/`, via **FastAPI**.
- **`core/`**: Infraestrutura do sistema — variáveis de ambiente (`config.py`), logging em disco (`logger.py`), exceções customizadas, identificadores dos canais (`identity.py`), vínculo de contas de canal com a API (`account_link.py`) e um `SecurityManager` para criptografia simétrica (Fernet), hash (SHA-256) e senhas (bcrypt).
- **`database/`**: **SQLAlchemy** + **PostgreSQL**. Define as tabelas (Models) para Usuários, Histórico, Sessões de Chat e códigos de vínculo. Em `migrations/` fica o script que converte os IDs gravados antes do prefixo de canal.
- **`llm/`**: Design Pattern _Strategy_ para trocar de provedor de LLM sem alterar os agentes:
  - **OpenAI** (GPT-4o)
  - **Anthropic** (Claude Opus 5)
  - **Google Gemini** (gemini-2.5-flash)
  - **Ollama** (modelos locais via HTTP).
- **`memory/`**: Memória do agente:
  - _Curto prazo_: buffer de histórico da conversa, gravado no Postgres e recarregado depois de um restart.
  - _Longo prazo (RAG)_: **ChromaDB** (`vector.py`). Cada troca (mensagem + resposta) vira uma lembrança do usuário. A cada mensagem, o agente busca as lembranças mais parecidas **do mesmo usuário** e as usa no Planner e na resposta. Os embeddings são gerados localmente pelo ChromaDB (modelo `all-MiniLM-L6-v2`, ~80 MB baixados no primeiro uso), então funcionam com qualquer LLM.
  - _Cache_: **Memcached** (`cache.py`). Deduplica os webhooks do Telegram e guarda por 1 hora a intenção detectada de cada texto, economizando uma chamada de LLM em mensagens repetidas.
  - ChromaDB e Memcached são opcionais: fora do ar, o agente segue só com o histórico recente.
- **`models/`**: _Data classes_ para tipar os dados que circulam entre as camadas.
- **`tools/`**: Catálogo de ferramentas descobertas automaticamente pelo Registry. Inclui:
  - Web Search (DuckDuckGo)
  - SMTP Mailer e notificações via Telegram, só para os destinatários liberados em `EMAIL_ALLOWED_RECIPIENTS` e `TELEGRAM_ALLOWED_CHAT_IDS`
  - Criptografia simétrica (Fernet)
  - Processamento de imagem (Pillow+OpenCV), anonimização facial e detecção de adulteração (ELA/tamper)
  - Análise de áudio via Librosa

---

## 🚀 Como Executar Localmente

### 1. Infraestrutura Base (Docker)

O sistema exige o PostgreSQL. O ChromaDB (memória de longo prazo) e o Memcached (cache) são opcionais: sem eles, o agente perde as lembranças de conversas antigas e a deduplicação de webhooks usa a memória do processo. Inicie-os isoladamente com o Docker:

```bash
docker-compose up -d
```

_(Isso iniciará o PostgreSQL na porta 5432, ChromaDB na 8000 e o Memcached na 11211)._

### 2. Preparação do Ambiente Python

Crie o ambiente virtual e instale as dependências de backend (todas com versão fixa no `requirements.txt`):

```bash
python3 -m venv venv
source venv/bin/activate  # Em Mac/Linux
# venv\Scripts\activate   # Em Windows

pip install -r requirements.txt
```

### 3. Variáveis de Ambiente

Crie um arquivo `.env` na raiz do repositório baseado nos apontamentos do arquivo `core/config.py`.
Exemplo básico:

```ini
# Chaves API (Deixe em branco as que não for usar)
OPENAI_API_KEY=sk-xxxxxxxxxxx
TELEGRAM_BOT_TOKEN=000000:XXXXXXXXXX

# Banco de Dados
POSTGRES_USER=admin
POSTGRES_PASSWORD=adminpassword
POSTGRES_DB=mvp_agente
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# Autenticação (JWT) das rotas REST — gere com: openssl rand -hex 32
JWT_SECRET_KEY=troque-por-uma-chave-secreta-aleatoria
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

### 4. Ligando os Motores

A arquitetura oferece dois pontos de entrada para inicialização do ecossistema:

- **Modo Web Server / Webhooks (API)**
  Sobe a API construída no FastAPI escutando requisições, por exemplo, originadas pela API do Telegram:

  ```bash
  python app.py
  ```

  _(Acessível localmente em `http://0.0.0.0:8080`)_

- **Modo CLI / Teste Interativo**
  Para testar o fluxo Multi-Agent localmente. Simula uma interface de terminal para você conversar diretamente com o orquestrador.
  ```bash
  python main.py
  ```

### 5. Autenticação da API

As rotas REST de chat (`/api/v1/chat/*`) exigem um token JWT.
Os bots (Telegram/Discord) não passam por aqui — eles chamam o orquestrador diretamente em
processo. O token é necessário apenas para quem consome a API HTTP (clientes
externos):

```bash
# 1. Registrar um usuário e já receber o token
curl -X POST http://localhost:8080/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"external_id": "meu-usuario", "password": "minha-senha"}'

# 2. Nas próximas vezes, autenticar via login (form OAuth2: username=external_id)
curl -X POST http://localhost:8080/api/v1/auth/login \
  -d "username=meu-usuario&password=minha-senha"

# 3. Usar o access_token retornado no header das demais chamadas
curl http://localhost:8080/api/v1/chat/sessions \
  -H "Authorization: Bearer <access_token>"
```

#### Ver pela API as conversas do Telegram ou do Discord

Quem usa um bot não tem senha. Para entrar na API com a mesma conta:

1. Mande `/vincular` para o bot **em conversa privada**. Ele responde com um código que vale 10 minutos e só pode ser usado uma vez.
2. Troque o código por uma senha. A resposta traz o token e o `external_id` da conta (ex: `telegram:123`):

   ```bash
   curl -X POST http://localhost:8080/api/v1/auth/link \
     -H "Content-Type: application/json" \
     -d '{"code": "ABCD2345EF", "password": "minha-senha"}'
   ```

3. Nas próximas vezes, faça login com esse `external_id` e a senha. Esqueceu a senha? Repita os passos.

Em grupos, cada membro tem a própria sessão de conversa com o agente.

### 6. Atualizando um banco criado antes do prefixo de canal

Se o banco tem dados de antes de 2026-09-25, os IDs antigos (ex: `123`) não se ligam aos novos (`telegram:123`). Para converter, e também apagar a tabela `events` do calendário removido:

```bash
python -m database.migrations.prefix_channel_ids --drop-events          # só mostra o que faria
python -m database.migrations.prefix_channel_ids --drop-events --apply  # grava
```

## 📄 Licença

Distribuído sob a licença MIT. Veja [LICENSE](LICENSE) para mais detalhes.

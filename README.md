# MVP Agente

Orquestrador multi-agentes em Python, projetado para atuar em diversos canais (Telegram, WhatsApp, Web), integrando memória de curto/longo prazo, banco relacional e um catálogo de ferramentas (busca, e-mail, forense de imagem/áudio).

Este é um MVP em desenvolvimento ativo: a arquitetura segue padrões conhecidos (Strategy para os LLMs, injeção de dependências entre agentes, registry com auto-discovery de tools). Já existe uma suíte de testes automatizada (pytest + SQLite em memória, veja `tests/`) e autenticação JWT nas rotas REST, mas ainda não há hardening completo de produção — trate como base sólida para evoluir.

---

## 🏗 Arquitetura do Projeto

O sistema é modular, aplicando alguns padrões de Engenharia de Software (injeção de dependências, Strategy):

- **`agents/`**: Padrão _Multi-Agent_ simples, onde:
  - **Manager**: Conversa com o usuário e orquestra o fluxo.
  - **Planner**: Recebe o objetivo e o catálogo de tools, e desenha um plano de ação (JSON/Pipeline).
  - **Executor**: Executa as funções Python indicadas no plano.
- **`channels/`**: Camada de _Gateway_. Recebe Webhooks externos (ex: Telegram) e normaliza os payloads. O arquivo principal `app.py` expõe esses endpoints via **FastAPI**.
- **`core/`**: Infraestrutura do sistema — variáveis de ambiente (`config.py`), logging em disco (`logger.py`), exceções customizadas e um `SecurityManager` para criptografia simétrica (Fernet) e hash (SHA-256).
- **`database/`**: **SQLAlchemy** + **PostgreSQL**. Define as tabelas (Models) para Usuários, Histórico e Sessões de Chat.
- **`llm/`**: Design Pattern _Strategy_ para trocar de provedor de LLM sem alterar os agentes:
  - **OpenAI** (GPT-4o, GPT-3.5)
  - **Anthropic** (Claude)
  - **Ollama** (modelos locais via HTTP).
- **`memory/`**: Três mecanismos de memória:
  - _Curto prazo_: buffer de histórico da conversa.
  - _Longo prazo (RAG)_: busca semântica via **ChromaDB**.
  - _Cache/velocidade_: **Memcached** (caches rápidos, rate limits).
- **`models/`**: _Data classes_ para tipar os dados que circulam entre as camadas.
- **`tools/`**: Catálogo de ferramentas descobertas automaticamente pelo Registry. Inclui:
  - Web Search (DuckDuckGo)
  - SMTP Mailer e notificações via Telegram
  - Criptografia simétrica (Fernet)
  - Processamento de imagem (Pillow+OpenCV), anonimização facial e detecção de adulteração (ELA/tamper)
  - Análise de áudio via Librosa

---

## 🚀 Como Executar Localmente

### 1. Infraestrutura Base (Docker)

O sistema exige que o banco relacional, o banco de vetores e a memória cache estejam ativos. Inicie-os isoladamente com o Docker:

```bash
docker-compose up -d
```

_(Isso iniciará o PostgreSQL na porta 5432, ChromaDB na 8000 e o Memcached na 11211)._

### 2. Preparação do Ambiente Python

Crie o ambiente virtual e instale as mais de 15 dependências de backend:

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

As rotas REST de calendário e chat (`/api/v1/calendar/*`, `/api/v1/chat/*`) exigem um token JWT.
Os bots (Telegram/Discord) não passam por aqui — eles chamam o orquestrador diretamente em
processo. O token é necessário apenas para quem consome a API HTTP (o front-end em `ui/` ou
clientes externos):

```bash
# 1. Registrar um usuário e já receber o token
curl -X POST http://localhost:8080/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"external_id": "meu-usuario", "password": "minha-senha"}'

# 2. Nas próximas vezes, autenticar via login (form OAuth2: username=external_id)
curl -X POST http://localhost:8080/api/v1/auth/login \
  -d "username=meu-usuario&password=minha-senha"

# 3. Usar o access_token retornado no header das demais chamadas
curl http://localhost:8080/api/v1/calendar/events \
  -H "Authorization: Bearer <access_token>"
```

## 📄 Licença

Distribuído sob a licença MIT. Veja [LICENSE](LICENSE) para mais detalhes.

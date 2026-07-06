# 🤖 MVP Agente - Inteligência Artificial Corporativa

Este repositório contém a arquitetura completa e de nível de produção para o **MVP Agente**, um orquestrador multi-agentes projetado para atuar em diversos canais (Telegram, WhatsApp, Web), integrando memórias avançadas, bancos de dados, ferramentas forenses e de comunicação externa.

---

## 🏗 Arquitetura do Projeto

O sistema foi estruturado de forma modular e escalável, aplicando padrões rigorosos de Engenharia de Software (SOLID, Injeção de Dependências, Strategy):

- **`agents/`**: O "cérebro" inteligente. Segue um padrão _Multi-Agent_ onde:
  - **Manager**: Conversa amigavelmente com o usuário e orquestra o fluxo.
  - **Planner**: Pensa friamente e desenha o plano de ação (JSON/Pipeline).
  - **Executor**: Executa cegamente as funções em Python requeridas no plano.
- **`channels/`**: A camada de _Gateway_. Recebe Webhooks externos (ex: Telegram) e normaliza os payloads. O arquivo principal `app.py` expõe esses endpoints de entrada via **FastAPI**.
- **`core/`**: O pilar de infraestrutura do sistema. Contém o motor central de variáveis de ambiente (`config.py`), um sistema profissional de logs salvos em disco (`logger.py`), controle de exceções arquiteturais e um `SecurityManager` nativo para criptografia simétrica e Hash (SHA-256).
- **`database/`**: Motor relacional utilizando **SQLAlchemy** e **PostgreSQL**. Define as tabelas (Models) e migrações (Alembic) para rastrear Usuários, Histórico Bruto e Sessões de Chat com segurança.
- **`llm/`**: Baseado no Design Pattern _Strategy_. Oferece acoplamento nativo a múltiplos motores de inteligência, sendo extremamente fácil trocar de cérebro sem alterar o projeto:
  - **OpenAI** (GPT-4o, GPT-3.5)
  - **Anthropic** (Claude 3 Opus/Sonnet)
  - **Ollama** (Modelos open-source locais via HTTP para 100% de privacidade).
- **`memory/`**: Sistema triplo de recordação de eventos:
  - _Curto Prazo_: Buffer contextual gerenciado ativamente.
  - _Longo Prazo (RAG)_: Busca semântica acelerada utilizando os vetores nativos do **ChromaDB**.
  - _Curto Prazo/Velocidade_: Gerenciamento em alta performance no **Memcached** (Caches rápidos, Rate Limits).
- **`models/`**: _Data classes_ para garantir a tipagem rígida dos dados que circulam entre as pastas.
- **`tools/`**: O verdadeiro arsenal de superpoderes do Agente (Registry). O catálogo atual inclui:
  - 🔎 Web Search DuckDuckGo, Automação do Google Calendar
  - 📧 SMTP Mailer (com envio criptografado) e Notificações (Telegram Sender)
  - 🔐 Criptografia Militar de mão dupla (Fernet)
  - 📸 Forense Visual: Processador Híbrido (Pillow+OpenCV), Anonimizador Facial Seguro e Detector de Adulteração (Tamper/ELA).
  - 🎙️ Analisador de Áudio via Librosa (Frequência e Conteúdo Sensível).

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

pip install -r requeires.txt
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
```

### 4. Ligando os Motores

A arquitetura oferece dois pontos de entrada para inicialização do ecossistema:

- **Modo Web Server / Webhooks (API)**
  Para ambiente de produção. Sobe a API construída no FastAPI escutando requisições, por exemplo, originadas pela API do Telegram:

  ```bash
  python app.py
  ```

  _(Acessível localmente em `http://0.0.0.0:8080`)_

- **Modo CLI / Teste Interativo**
  Para testar o fluxo Multi-Agent localmente. Simula uma interface de terminal para você conversar diretamente com o orquestrador.
  ```bash
  python main.py
  ```

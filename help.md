# Pontos que não fazem sentido no sistema

_Revisão atualizada em 2026-09-25. Todos os itens foram tratados: os 15 da revisão anterior e as 7 pendências que dependiam de decisão. Nada disso foi commitado ainda._

## ✅ Resolvidos pela remoção do front-end e do calendário

- A ferramenta de agenda gravava tudo no `user_id` 1: o `calendar_manager` foi removido.
- Os lembretes não faziam nada: o `core/scheduler.py` foi removido.
- O front-end pedia um `external_id` que o backend ignorava: a pasta `ui/` foi removida.
- As referências a `calendar` em `app.py` e a `check_availability` no prompt do Planner foram removidas, junto com o CORS, que só servia ao front-end.

## ✅ Graves: identidade e segurança (corrigidos)

1. **Sessão de outra pessoa:** o `POST /api/v1/chat/sessions/{session_id}/messages` confere o dono da sessão (404 se for de outro usuário) e recusa com 422 os prefixos de canal (`telegram_`, `discord_`, `cli_`).
2. **Tomar conta criada por bot:** o `/register` recusa qualquer `external_id` existente. Os canais gravam IDs com prefixo (`telegram:123`, em `core/identity.py`), e a API não aceita `:` no `external_id`.
3. **`file_read` lendo qualquer arquivo:** só lê dentro de `FILE_READ_BASE_DIR` (padrão `data/files`). Recusa `..`, caminho absoluto e link simbólico que saia da pasta.
4. **Webhook do Telegram sem autenticação:** exige `TELEGRAM_WEBHOOK_SECRET` no header `X-Telegram-Bot-Api-Secret-Token`. Fora de `development`, sem o segredo, recusa tudo.
5. **Senhas em SHA-256:** passaram para bcrypt. Senhas antigas migram no primeiro login certo.

## ✅ Lógica do agente (corrigida)

6. **Erros do LLM:** os provedores (`llm/*.py`) lançam `LLMException` em vez de devolver `{"status":"error"}` ou uma frase de erro. Agora os fallbacks de `intent.py`, `reasoning.py` e `planner.py` rodam de verdade.
7. **Atalho de saudação:** o prompt do IntentDetector manda usar exatamente `Greeting` e `SmallTalk`, os rótulos que o ReasoningEngine procura. Um "oi" volta a pular o raciocínio e o Planner.
8. **Planner às cegas:** o Planner recebe a mensagem original, o histórico recente e a data e hora atuais, além do objetivo resumido.
9. **Histórico perdido no restart:** a `ConversationMemory` recarrega do Postgres a sessão que não está na memória.
10. **Webhook travando o servidor:** o Telegram roda `process_message` numa thread (`asyncio.to_thread`), como o Discord já fazia.
11. **Erro virando fala do assistente:** com o item 6, uma falha do LLM interrompe a mensagem antes de ser salva. O canal responde com a mensagem genérica de erro, e o histórico não é poluído.
- **Bug novo encontrado e corrigido:** o `ContextBuilder` passava objetos `Message` (com `datetime`) para o ReasoningEngine, que fazia `json.dumps` e quebrava a partir da segunda mensagem de qualquer conversa. O erro era engolido e tudo caía no Planner. Agora o histórico vai como dicionários simples.

## ✅ Documentação e config (corrigidas)

12. **README:** agora diz que o ChromaDB e o cache do Memcached têm cliente pronto, mas ainda não estão ligados ao agente. Lista os canais reais (Telegram, Discord, CLI, API) e o Gemini. `SYSTEM_PROMPT_EXECUTOR` e `models/tool.py`, que não eram usados, foram removidos.
13. **`.env.exemplo`:**
    - Saíram `ENCRYPTION_KEY` e `MASTER_ENCRYPTION_KEY` (sem uso).
    - `LOG_LEVEL` agora controla o console.
    - Entraram `ENVIRONMENT`, `SMTP_*`, `OLLAMA_*`, `WEBHOOK_URL`, `TELEGRAM_WEBHOOK_SECRET` e `FILE_READ_BASE_DIR`.
14. **Factory de LLM:**
    - Os comentários descrevem a ordem real (OpenAI > Anthropic > Ollama > Gemini).
    - As chaves de exemplo ficaram vazias, então a falsa `sk-…` não ativa mais a OpenAI.
    - O Claude padrão passou a ser `claude-opus-5`, com `fallbacks: "default"` para recusas por segurança.
    - A menção a "Gemini 1.5" foi corrigida.
15. **Detalhes menores:**
    - `Makefile` corrigido (`requirements.txt`).
    - A deduplicação em memória do webhook guarda no máximo 10.000 IDs.
    - `get_current_user` responde 503, e não 500, com o banco fora do ar.
    - `conteudo` virou `content`.
- **Instalação quebrada, encontrada e corrigida:** a URL do banco agora força o driver `psycopg2` (`postgresql+psycopg2://`). No SQLAlchemy 2.1, que o `pip` instala hoje, `postgresql://` procura o psycopg 3, que não está no `requirements.txt`.

## ✅ Pendências decididas e resolvidas

16. **`email_sender` e `telegram_sender` liberados para qualquer pessoa:** decidido usar destinatários permitidos.
    - `EMAIL_ALLOWED_RECIPIENTS` aceita endereços e domínios (`@empresa.com`).
    - `TELEGRAM_ALLOWED_CHAT_IDS` aceita chat_ids e @usernames.
    - Lista vazia = envio desligado.
    - No e-mail, todos os destinatários precisam estar liberados, e quebras de linha no campo são recusadas (evita injetar `Bcc:`).
17. **Vincular conta de bot à API:** o usuário manda `/vincular` ao bot em conversa privada e recebe um código de uso único, válido por 10 minutos (só o hash fica no banco, tabela `account_link_codes`). Com ele, `POST /api/v1/auth/link` define a senha e devolve o token e o `external_id` (ex: `telegram:123`). O mesmo fluxo serve para trocar a senha. Em grupo, o bot não manda o código. O comando não passa pelo agente, então o código não vai para o LLM nem para o histórico.
18. **Dados antigos sem prefixo:** o script `python -m database.migrations.prefix_channel_ids` converte os IDs (`123` → `telegram:123`, `user_terminal` → `cli:terminal`, sessão `123` → `telegram_123`, `sessao_cli_local` → `cli_local`).
    - O canal de cada usuário numérico é deduzido pelas sessões dele. Os casos sem como decidir são pulados e aparecem no relatório.
    - Se o ID novo já existir, os dados são juntados.
    - Sem `--apply`, o script só mostra o que faria.
19. **Sessão de grupo do Telegram:** em grupo, cada membro tem a própria sessão (`telegram_<grupo>_<usuário>`). O Discord segue a mesma regra nos canais de servidor. Em conversa privada, nada muda.
20. **Tabela `events` órfã:** o mesmo script remove com `--drop-events`.
21. **Dependências sem versão:** `requirements.txt` e `requirements-dev.txt` têm versões fixas, as mesmas testadas numa instalação limpa. A imagem do ChromaDB no `docker-compose.yml` foi fixada na versão do cliente (`1.5.9`).
22. **RAG e cache:** decidido ligar os dois ao agente.
    - **ChromaDB:** cada troca (mensagem + resposta) vira uma lembrança com o `user_id`. A cada mensagem, o `ContextBuilder` busca as 3 lembranças mais parecidas **do mesmo usuário** e descarta as pouco relevantes. Elas vão para o Planner e para a resposta final.
    - Os embeddings são gerados no próprio processo (modelo `all-MiniLM-L6-v2`, ~80 MB baixados no primeiro uso), então funcionam com qualquer LLM.
    - **Memcached:** guarda por 1 hora a intenção detectada de cada texto. Também faz a deduplicação do webhook, agora com `add` atômico.
    - Os dois são opcionais. Fora do ar, o agente segue sem eles, e o ChromaDB só tenta reconectar depois de 60s.
    - `models/memory.py`, que não era usado, foi removido.

## Para aplicar num ambiente existente

- Reinstale as dependências (`pip install -r requirements.txt`): as versões mudaram.
- Preencha `EMAIL_ALLOWED_RECIPIENTS` e `TELEGRAM_ALLOWED_CHAT_IDS` no `.env`. Sem elas, as ferramentas de envio recusam tudo.
- Se o banco tem dados antigos, rode `python -m database.migrations.prefix_channel_ids --drop-events` para conferir e depois repita com `--apply`.
- A tabela `account_link_codes` é criada sozinha na subida da API (`create_all`).

## Como validar

Os testes (`tests/`, 74 no total) passam num ambiente Python 3.12 limpo, instalado com as versões fixas. Os das pendências resolvidas nesta rodada estão em `test_account_link.py`, `test_sender_allowlist.py`, `test_long_term_memory.py` e `test_migrate_channel_ids.py`.

Também foram conferidos fora dos testes:
- O RAG contra um ChromaDB real: cada usuário recupera só as próprias lembranças.
- O cache contra o Memcached do `docker-compose`, inclusive com ele fora do ar.
- O script de migração em modo simulação contra o Postgres local.

# Pontos que não fazem sentido no sistema

_Revisão atualizada em 2026-09-25, depois da remoção do front-end (`ui/`) e do módulo de calendário e da correção dos itens graves._

## Resolvidos pela remoção

- ~~A ferramenta de agenda não sabia quem era o usuário (gravava tudo no `user_id` 1).~~ O `calendar_manager` foi removido.
- ~~Os lembretes não faziam nada.~~ O `core/scheduler.py` foi removido.
- ~~O front-end pedia um `external_id` que o backend ignorava.~~ A pasta `ui/` foi removida.
- ~~`app.py` importava `calendar` duas vezes e o prompt do Planner citava `check_availability`.~~ As duas referências foram removidas.
- ~~`CORS_ORIGINS` faltava no `.env.exemplo`.~~ O CORS saiu junto com o front-end.

## 🔴 Graves: identidade e segurança

Os cinco itens abaixo foram corrigidos em 2026-09-25 e têm testes em `tests/`.

1. ~~**Dá para escrever na sessão de outra pessoa.**~~ **Corrigido.** O `POST /api/v1/chat/sessions/{session_id}/messages` agora confere o dono da sessão, como o `GET` já fazia: sessão de outro usuário responde 404. Também recusa (422) `session_id` com prefixo de canal (`telegram_`, `discord_`, `cli_`), para ninguém criar pela API a sessão de um canal antes dele.
2. ~~**Qualquer um pode assumir uma conta criada pelos bots.**~~ **Corrigido.** O `/register` responde 409 para qualquer `external_id` que já exista, inclusive os criados por bot sem senha. Os canais passaram a gravar IDs com prefixo (`telegram:123`, `discord:456`, `cli:terminal`, em `core/identity.py`), e a API recusa `external_id` com `:`. Assim ninguém registra antes o ID de alguém que ainda vai falar com o bot.
3. ~~**`file_read` lê qualquer arquivo do servidor.**~~ **Corrigido.** A ferramenta só lê dentro de `FILE_READ_BASE_DIR` (padrão `data/files`, fora do git). `..`, caminhos absolutos e links simbólicos que saem da pasta são recusados.
4. ~~**Webhook do Telegram sem autenticação.**~~ **Corrigido.** O `set_webhook` envia `TELEGRAM_WEBHOOK_SECRET`, e cada update precisa trazer o mesmo valor no header `X-Telegram-Bot-Api-Secret-Token` (403 se não trouxer). Fora de `development`, sem o segredo configurado, o webhook recusa tudo.
5. ~~**As senhas usam SHA-256 com salt.**~~ **Corrigido.** Senhas novas usam bcrypt (`SecurityManager.hash_password`). Senhas antigas continuam funcionando: no primeiro login certo, são convertidas para bcrypt e o `password_salt` é zerado.

### Ainda em aberto

- **`email_sender` e `telegram_sender` continuam liberados para qualquer pessoa** que fale com o bot, que pode usar seu SMTP e seu bot para mandar mensagens. Falta decidir quem pode usar essas ferramentas (lista de usuários autorizados, destinatários permitidos ou desligar nos canais públicos).
- **Não há como vincular uma conta de bot à API.** Com o item 2, um usuário do Telegram não consegue mais definir senha para ver o próprio histórico pela API. Isso exige um fluxo de verificação (ex: código enviado pelo próprio bot).
- **Os dados antigos ficaram com os IDs sem prefixo.** Usuários e sessões gravados antes da mudança (ex: `123`) não se ligam aos novos (`telegram:123`, `telegram_123`), então o histórico antigo não aparece para eles. Se esse histórico importar, é preciso migrar o banco.
- **Em grupos do Telegram, a sessão é do grupo:** as mensagens de todos os membros entram na mesma sessão, que pertence a quem falou primeiro.

## 🟠 A lógica do agente não fecha

6. **Os erros do LLM não viram exceção.** Os `generate_json` devolvem `{"status":"error"}` em vez de lançar erro, então os `except` com fallback em `intent.py` e `reasoning.py` nunca rodam. Sem o campo `decision`, o Manager cai em `direct_response` (`agents/manager.py:45`). É o contrário do fallback do ReasoningEngine, que manda para o `planner` "por segurança".
7. **O atalho de saudação nunca dispara.** `core/cognitive/reasoning.py:22` procura `Greeting` ou `SmallTalk`, mas o prompt do IntentDetector (`core/cognitive/intent.py:32`) só dá exemplos como `Info.Query` e `Email.Send`. Na prática, um "oi" custa 3 a 4 chamadas de LLM.
8. **O Planner trabalha às cegas:**
   - Recebe só o `objective` resumido, não a mensagem original, então perde detalhes (destinatários, termos de busca).
   - Não recebe o histórico da conversa.
   - Não sabe a data de hoje, então não consegue resolver pedidos como "notícias de ontem".
9. **O histórico se perde ao reiniciar.** O comentário em `memory/conversation.py:13` diz que as mensagens são persistidas para sobreviver a reinícios. Elas são gravadas no Postgres, mas nunca relidas: depois de um restart, o agente esquece tudo.
10. **O webhook do Telegram trava o servidor.** `app.py:133` chama `manager.process_message`, que é bloqueante, dentro de um endpoint `async`. Enquanto o LLM responde, o servidor fica parado. O Discord já resolve isso com `to_thread`.
11. **Mensagens de erro viram resposta do assistente.** Um texto como "Erro na comunicação com a OpenAI…" é salvo no histórico como fala do assistente.

## 🟡 Documentação e config inconsistentes

12. **O README promete RAG (ChromaDB) e cache (Memcached) como memória do agente,** mas `VectorMemory` e `CacheMemory` não são usados em lugar nenhum. O mesmo vale para `models/tool.py` e `SYSTEM_PROMPT_EXECUTOR` (importado, nunca usado).
13. **`.env.exemplo` diverge de `core/config.py`:**
    - Define `ENCRYPTION_KEY`, mas o código lê `MASTER_ENCRYPTION_KEY`, que também não é usada.
    - `LOG_LEVEL` é ignorado.
    - Faltam `SMTP_*`, `WEBHOOK_URL`, `ENVIRONMENT` e `OLLAMA_*`.
14. **A factory de LLM se contradiz:**
    - O comentário diz que o Ollama tem prioridade "antes da nuvem", mas ele é o 3º da lista.
    - A chave de exemplo `sk-suachaveaqui…` passa na checagem `startswith("sk-")`.
    - O Claude padrão é `claude-3-opus-20240229`, um modelo já descontinuado.
    - O Gemini aparece como "1.5" nos comentários, mas o padrão é `gemini-2.5-flash`.
15. **Detalhes menores:**
    - `Makefile:6` tem o erro de digitação `requeires.txt`, então `make install` quebra.
    - `processed_updates_ram` (`app.py:44`) cresce sem limite.
    - `get_current_user` quebra com erro 500 se o banco estiver fora do ar.
    - Há identificadores em português, como `conteudo`, contrariando o `AGENTS.md`.
    - Se o banco já tinha a tabela `events`, ela continua lá (o `create_all` não apaga tabelas). Remova com `DROP TABLE events;`.

## Recomendação

Os itens graves foram corrigidos. O próximo passo é decidir quem pode usar `email_sender` e `telegram_sender` (primeiro item de "Ainda em aberto"). Depois, vale atacar o item 6: sem ele, uma falha do LLM passa despercebida e o agente responde como se nada tivesse acontecido.

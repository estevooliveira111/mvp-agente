import asyncio
import secrets
from collections import OrderedDict
import uvicorn
from fastapi import FastAPI, HTTPException, Request
from core.logger import logger
from core.config import settings
from core.agent_bootstrap import cache, manager
from core.account_link import is_link_command, link_command_reply
from core.identity import channel_user_id, conversation_session_id
from core.ngrok import discover_public_url

from telegram import Update, Bot
import sys
import os

# Ajuste de path para importação local se necessário
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# ==========================================
# Inicialização do Servidor FastAPI
# ==========================================
app = FastAPI(
    title="MVP Agente - API Gateway",
    description="Interface de Webhooks robusta com deduplicação para conectar canais com a IA.",
    version="1.1.0"
)

try:
    from api.routes import chat
    app.include_router(chat.router)
except Exception as e:
    logger.error(f"Não foi possível carregar rotas do chat: {e}")

try:
    from api.routes import auth
    app.include_router(auth.router)
except Exception as e:
    logger.error(f"Não foi possível carregar rotas de autenticação: {e}")

# ==========================================
# Deduplicação de updates
# ==========================================
# O Memcached (cache do agent_bootstrap) é o principal. Se ele não conectar, usa a memória
# do processo, limitada aos últimos PROCESSED_UPDATES_MAX update_ids (o Telegram só
# reenvia updates recentes).
PROCESSED_UPDATES_MAX = 10000
processed_updates_ram = OrderedDict()


def already_processed_in_ram(update_id: str) -> bool:
    """Marca o update como processado e diz se ele já tinha sido visto."""
    if update_id in processed_updates_ram:
        return True
    processed_updates_ram[update_id] = True
    if len(processed_updates_ram) > PROCESSED_UPDATES_MAX:
        processed_updates_ram.popitem(last=False)
    return False

from database.database import engine, Base
import database.models  # Garante que os models estão registrados no Base.metadata

from channels.discord_bot import start_discord_bot_background

@app.on_event("startup")
async def startup_event():
    logger.info("🚀 Servidor FastAPI iniciado! API pronta para receber eventos dos Canais (Webhooks).")
    
    # Cria as tabelas do banco de dados caso não existam
    if engine:
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Estrutura do banco de dados sincronizada.")
    
    # Inicia o worker do Discord em background
    logger.info("Iniciando bot do Discord...")
    start_discord_bot_background()

    public_url = settings.WEBHOOK_URL
    if settings.TELEGRAM_BOT_TOKEN and not public_url:
        # Sem WEBHOOK_URL fixa, usa o túnel do ngrok (ex: 'make dev'), se houver um.
        public_url = await asyncio.to_thread(
            discover_public_url, settings.NGROK_API_URL, settings.API_PORT
        )
        if public_url:
            logger.info(f"🌐 URL pública do ngrok detectada: {public_url}")

    if settings.TELEGRAM_BOT_TOKEN and public_url:
        try:
            async with Bot(token=settings.TELEGRAM_BOT_TOKEN) as bot:
                webhook_url = f"{public_url.rstrip('/')}/webhook/telegram"
                # O Telegram devolve esse segredo no header de cada update (ver telegram_webhook).
                await bot.set_webhook(
                    url=webhook_url,
                    secret_token=settings.TELEGRAM_WEBHOOK_SECRET or None,
                )
                logger.info(f"✅ Webhook do Telegram registrado automaticamente em: {webhook_url}")
        except Exception as e:
            logger.error(f"❌ Falha ao registrar webhook do Telegram automaticamente: {e}")

@app.get("/health")
async def health_check():
    return {"status": "online", "message": "O Cérebro da IA está ativo."}

@app.post("/webhook/telegram")
async def telegram_webhook(request: Request):
    """
    Endpoint de Inbound Webhook Seguro (Telegram Oficial).
    Utiliza Deduplicação Distribuída (Memcached) para evitar mensagens clones.
    """
    # Sem essa checagem, qualquer um poderia postar um update falso se passando
    # por qualquer usuário do Telegram.
    if settings.TELEGRAM_WEBHOOK_SECRET:
        received_secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
        if not secrets.compare_digest(received_secret, settings.TELEGRAM_WEBHOOK_SECRET):
            logger.warning("Webhook Bloqueado: secret token do Telegram ausente ou inválido.")
            raise HTTPException(status_code=403, detail="Secret token inválido.")
    elif settings.ENVIRONMENT != "development":
        logger.error("Webhook Bloqueado: TELEGRAM_WEBHOOK_SECRET não configurado fora de 'development'.")
        raise HTTPException(status_code=403, detail="Webhook não configurado.")

    try:
        data = await request.json()
    except Exception:
        return {"status": "error", "message": "Payload JSON inválido."}
        
    logger.info("Webhook (Inbound) acionado via Telegram")
    
    # O PTB v20+ exige um contexto assíncrono para o Bot
    async with Bot(token=settings.TELEGRAM_BOT_TOKEN) as bot:
        try:
            update = Update.de_json(data, bot)
        except Exception as e:
            logger.error(f"Erro ao converter Update usando lib oficial: {e}")
            return {"status": "error", "message": "Formato de Update inválido."}
            
        update_id = str(update.update_id)
        
        # ==========================================
        # Deduplicação (Prevenção de Clones e Loops)
        # ==========================================
        # 'add' é atômico: se dois reenvios chegarem juntos, só um passa. TTL de 2 horas.
        stored = cache.add(f"telegram_update_{update_id}", "1", ttl_seconds=7200)
        if stored is False:
            logger.warning(f"Webhook Bloqueado: Update {update_id} já foi processado (Memcached).")
            return {"status": "success", "message": "Already processed"}
        if stored is None and already_processed_in_ram(update_id):
            # Memcached fora do ar: usa a memória do processo.
            return {"status": "success", "message": "Already processed"}
            
        # ==========================================
        # Processamento e Resposta
        # ==========================================
        if not update.message or not update.message.text:
            return {"status": "ignored", "reason": "No valid text message"}
            
        chat_id = str(update.message.chat_id)
        is_private = update.message.chat.type == "private"
        telegram_user_id = update.message.from_user.id
        user_id = channel_user_id("telegram", telegram_user_id)
        user_message = update.message.text.strip()
        
        logger.info(f"[Webhook] Mensagem recebida de {user_id}: {user_message}")
        
        try:
            if is_link_command(user_message):
                # Não passa pelo agente: o código não pode ir para o LLM nem para o histórico.
                agent_response = await asyncio.to_thread(link_command_reply, user_id, is_private)
            else:
                # process_message é bloqueante (várias chamadas de LLM): roda numa thread
                # para não travar o event loop e as outras requisições.
                agent_response = await asyncio.to_thread(
                    manager.process_message,
                    session_id=conversation_session_id("telegram", chat_id, telegram_user_id, is_private),
                    user_id=user_id,
                    raw_message=user_message
                )
        except Exception as e:
            logger.error(f"Falha interna do Agente: {e}")
            agent_response = "Ops, meu cérebro deu um erro temporário processando sua mensagem! ⚠️"
        
        # Envio oficial via pacote
        try:
            await bot.send_message(chat_id=chat_id, text=agent_response)
        except Exception as e:
            logger.error(f"Falha ao enviar resposta para o Telegram: {e}")
            
        return {"status": "success", "agent_processed": True}

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=settings.API_PORT, reload=True)

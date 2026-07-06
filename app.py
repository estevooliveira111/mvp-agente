import uvicorn
from fastapi import FastAPI, Request
from core.logger import logger
from core.config import settings
from llm.factory import get_active_llm
from memory.conversation import ConversationMemory
from agents.planner import PlannerAgent
from agents.executor import ExecutorAgent
from agents.manager import ManagerAgent
from tools.registry import load_all_tools

from telegram import Update, Bot
from pymemcache.client.base import Client

# ==========================================
# Inicialização do Servidor FastAPI
# ==========================================
app = FastAPI(
    title="MVP Agente - API Gateway",
    description="Interface de Webhooks robusta com deduplicação para conectar canais com a IA.",
    version="1.1.0"
)

# ==========================================
# Instâncias Globais da IA (Singletons)
# ==========================================
llm = get_active_llm()
memory = ConversationMemory()
planner = PlannerAgent(llm_client=llm)

tools_registry, tools_metadata = load_all_tools()
executor = ExecutorAgent(tools_registry=tools_registry)

manager = ManagerAgent(llm, memory, planner, executor, tools_metadata=tools_metadata)

# ==========================================
# Instância de Cache para Deduplicação
# ==========================================
try:
    cache = Client((settings.MEMCACHED_HOST, settings.MEMCACHED_PORT), connect_timeout=1, timeout=1)
except Exception:
    cache = None

processed_updates_ram = set() # Fallback de memória caso Memcached não conecte

@app.on_event("startup")
async def startup_event():
    logger.info("🚀 Servidor FastAPI iniciado! API pronta para receber eventos dos Canais (Webhooks).")

@app.get("/health")
async def health_check():
    return {"status": "online", "message": "O Cérebro da IA está ativo."}

@app.post("/webhook/telegram")
async def telegram_webhook(request: Request):
    """
    Endpoint de Inbound Webhook Seguro (Telegram Oficial).
    Utiliza Deduplicação Distribuída (Memcached) para evitar mensagens clones.
    """
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
        if cache:
            try:
                if cache.get(f"telegram_update_{update_id}"):
                    logger.warning(f"Webhook Bloqueado: Update {update_id} já foi processado (Memcached).")
                    return {"status": "success", "message": "Already processed"}
                # Salva no cache com TTL de 2 horas (7200s)
                cache.set(f"telegram_update_{update_id}", "1", expire=7200)
            except Exception as e:
                logger.error(f"Erro no Memcached: {e}. Usando RAM.")
                if update_id in processed_updates_ram:
                    return {"status": "success", "message": "Already processed"}
                processed_updates_ram.add(update_id)
        else:
            if update_id in processed_updates_ram:
                return {"status": "success", "message": "Already processed"}
            processed_updates_ram.add(update_id)
            
        # ==========================================
        # Processamento e Resposta
        # ==========================================
        if not update.message or not update.message.text:
            return {"status": "ignored", "reason": "No valid text message"}
            
        chat_id = str(update.message.chat_id)
        user_id = str(update.message.from_user.id)
        user_message = update.message.text.strip()
        
        logger.info(f"[Webhook] Mensagem recebida de {user_id}: {user_message}")
        
        try:
            agent_response = manager.process_message(
                session_id=chat_id,
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
    uvicorn.run("app:app", host="0.0.0.0", port=8080, reload=True)

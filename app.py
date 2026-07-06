import uvicorn
from fastapi import FastAPI, Request
from core.logger import logger
from llm.factory import get_active_llm
from memory.conversation import ConversationMemory
from agents.planner import PlannerAgent
from agents.executor import ExecutorAgent
from agents.manager import ManagerAgent

from tools.registry import load_all_tools

# ==========================================
# Inicialização do Servidor FastAPI
# ==========================================
app = FastAPI(
    title="MVP Agente - API Gateway",
    description="Interface de Webhooks para conectar o WhatsApp, Telegram, etc. com a IA.",
    version="1.0.0"
)

# ==========================================
# Instâncias Globais da IA (Singletons)
# ==========================================
# Ao instanciar fora das rotas, mantemos o estado da memória entre as requisições HTTP
llm = get_active_llm()
memory = ConversationMemory()
planner = PlannerAgent(llm_client=llm)

# Carrega todas as ferramentas da pasta tools dinamicamente
tools_registry, tools_metadata = load_all_tools()
executor = ExecutorAgent(tools_registry=tools_registry)

manager = ManagerAgent(llm, memory, planner, executor, tools_metadata=tools_metadata)

@app.on_event("startup")
async def startup_event():
    logger.info("🚀 Servidor FastAPI iniciado! API pronta para receber eventos dos Canais (Webhooks).")

@app.get("/health")
async def health_check():
    """Rota simples para o Docker e Balanceadores de Carga verificarem se a API está viva."""
    return {"status": "online", "message": "O Cérebro da IA está ativo."}

@app.post("/webhook/telegram")
async def telegram_webhook(request: Request):
    """
    Endpoint (Inbound) Oficial do Canal Telegram.
    Processa payloads JSON do webhook do Telegram, invoca a IA,
    e responde usando a ferramenta `telegram_sender`.
    """
    try:
        data = await request.json()
    except Exception:
        return {"status": "error", "message": "Payload JSON inválido."}
        
    logger.info("Webhook (Inbound) acionado via Telegram")
    
    # 1. Normalização da Carga (Lida com mensagens novas e editadas)
    message_data = data.get("message") or data.get("edited_message")
    
    if not message_data:
        # Pode ser um update de callback de botões, ou kick de grupo. Ignora no MVP.
        return {"status": "ignored", "reason": "Not a standard text message"}
        
    chat_id = str(message_data.get("chat", {}).get("id"))
    user_id = str(message_data.get("from", {}).get("id"))
    user_message = message_data.get("text", "").strip()
    
    if not chat_id or not user_message:
        return {"status": "ignored", "reason": "Message contains no text or missing chat_id"}
    
    # 2. Roteia o texto limpo para o Core Inteligente (ManagerAgent)
    try:
        agent_response = manager.process_message(
            session_id=chat_id,
            user_id=user_id,
            raw_message=user_message
        )
    except Exception as e:
        logger.error(f"Falha interna do Agente: {e}")
        agent_response = "Ops, meu cérebro deu um erro temporário processando sua mensagem! ⚠️"
    
    # 3. (Outbound) Responde de volta diretamente para o chat do usuário no Telegram
    # Importamos a ferramenta que criamos lá atrás!
    from tools.telegram_sender import execute as send_telegram_msg
    
    # Injeta a resposta do agente na ferramenta de Outbound
    outbound_result = send_telegram_msg(chat_id=chat_id, text=agent_response)
    logger.info(f"Telegram Sender Status: {outbound_result}")
    
    return {"status": "success", "agent_processed": True}

if __name__ == "__main__":
    # Roda o servidor Web na porta 8080 (Acesso via http://localhost:8080)
    uvicorn.run("app:app", host="0.0.0.0", port=8080, reload=True)

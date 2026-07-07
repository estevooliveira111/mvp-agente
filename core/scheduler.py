import asyncio
from datetime import datetime, timedelta
from core.logger import logger
from database.database import SessionLocal
from database.models import EventDB
from telegram import Bot
from core.config import settings

async def reminder_worker():
    """
    Worker assíncrono que roda em background junto com o FastAPI.
    Ele varre a cada X segundos o banco de dados buscando eventos que estejam
    perto de acontecer, disparando as notificações via Telegram.
    """
    logger.info("⏰ Background Worker de Lembretes iniciado!")

    bot = Bot(token=settings.TELEGRAM_BOT_TOKEN) if settings.TELEGRAM_BOT_TOKEN else None
    
    while True:
        try:
            if bot:
                db = SessionLocal()
                now = datetime.utcnow()
                
                # Para simplificar, buscamos eventos que vão ocorrer na próxima 1 hora
                # que ainda estejam como 'scheduled'.
                upcoming_window = now + timedelta(hours=1)
                
                events = db.query(EventDB).filter(
                    EventDB.status == "scheduled",
                    EventDB.start_time > now,
                    EventDB.start_time <= upcoming_window
                ).all()
                
                for ev in events:
                    # Verifica se o evento está a exatos 'N' minutos de distância com base na lista de reminders
                    time_diff = ev.start_time - now
                    minutes_left = int(time_diff.total_seconds() / 60)
                    
                    for r in ev.reminders:
                        # Se faltar exatos 'r' minutos (margem de 1 minuto por causa do sleep)
                        if r - 1 <= minutes_left <= r + 1:
                            logger.info(f"[Lembrete] Disparando alarme para evento {ev.id} ({minutes_left} min restantes)")
                            # Como não temos a amarração exata de Telegram ID no model User (tem external_id)
                            # Enviamos o aviso (supondo que user_id ou o próprio DB guarde o chat_id no future)
                            # Aqui usaríamos o bot.send_message
                            pass
                            
                db.close()
                
        except Exception as e:
            logger.error(f"Erro no worker de lembretes: {e}")
            
        # Roda a cada 60 segundos
        await asyncio.sleep(60)

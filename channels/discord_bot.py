import discord
import asyncio
from core.logger import logger
from core.config import settings
from core.agent_bootstrap import manager
from core.account_link import is_link_command, link_command_reply
from core.identity import channel_user_id, conversation_session_id

# Configurando Intents (necessários para ler conteúdo de mensagens no Discord moderno)
intents = discord.Intents.default()
intents.message_content = True

class MVPAgentDiscordBot(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def on_ready(self):
        logger.info(f"✅ Bot do Discord conectado como: {self.user} (ID: {self.user.id})")

    async def on_message(self, message):
        # Evitar loop infinito (não responder a si mesmo)
        if message.author.id == self.user.id:
            return

        # Para fins de simplificação, processamos todas as mensagens que o bot tem acesso
        # Em produção, você poderia restringir a uma menção: if self.user.mentioned_in(message):
        
        is_private = isinstance(message.channel, discord.DMChannel)
        session_id = conversation_session_id("discord", message.channel.id, message.author.id, is_private)
        user_id = channel_user_id("discord", message.author.id)
        raw_text = message.content.strip()

        if not raw_text:
            return
            
        logger.info(f"Mensagem recebida do Discord de {message.author} no canal {message.channel.id}")

        try:
            if is_link_command(raw_text):
                # Não passa pelo agente: o código não pode ir para o LLM nem para o histórico.
                reply = await asyncio.to_thread(link_command_reply, user_id, is_private)
                await message.channel.send(reply)
                return

            # Envia a notificação de que o bot está "digitando"
            async with message.channel.typing():
                # Processa usando o manager, rodando a função bloqueante num executor assíncrono
                response_text = await asyncio.to_thread(
                    manager.process_message,
                    session_id=session_id,
                    user_id=user_id,
                    raw_message=raw_text
                )
            
            # Divide mensagens longas (Discord limite de 2000 chars)
            if len(response_text) > 2000:
                chunks = [response_text[i:i+2000] for i in range(0, len(response_text), 2000)]
                for chunk in chunks:
                    await message.channel.send(chunk)
            else:
                await message.channel.send(response_text)

        except Exception as e:
            logger.error(f"Erro ao processar mensagem do Discord: {e}", exc_info=True)
            await message.channel.send("Desculpe, ocorreu um erro interno ao processar sua mensagem.")

def start_discord_bot_background():
    """Inicializa o bot do Discord num loop de eventos secundário ou tarefa assíncrona."""
    token = settings.DISCORD_BOT_TOKEN
    if not token:
        logger.warning("DISCORD_BOT_TOKEN não configurado. Bot do Discord inativo.")
        return

    client = MVPAgentDiscordBot(intents=intents)
    
    # O bot precisa rodar assincronamente.
    # No FastAPI (app.py), chamaremos essa função usando asyncio.create_task()
    asyncio.create_task(client.start(token))

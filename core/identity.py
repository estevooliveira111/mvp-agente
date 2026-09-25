"""
Identificadores de usuário e de sessão usados pelos canais (Telegram, Discord, CLI).

Os canais sempre gravam IDs com prefixo, para que um usuário da API REST não consiga
criar antes, com o mesmo valor, o usuário ou a sessão de alguém de um canal e depois
ler as mensagens dessa pessoa.
"""

CHANNEL_ID_SEPARATOR = ":"
CHANNELS = ("telegram", "discord", "cli")

# Prefixos de session_id reservados aos canais (ex: 'telegram_123').
RESERVED_SESSION_PREFIXES = tuple(f"{channel}_" for channel in CHANNELS)


def channel_user_id(channel: str, raw_id) -> str:
    """Ex: channel_user_id('telegram', 123) -> 'telegram:123'."""
    return f"{channel}{CHANNEL_ID_SEPARATOR}{raw_id}"


def channel_session_id(channel: str, raw_id) -> str:
    """Ex: channel_session_id('telegram', 123) -> 'telegram_123'."""
    return f"{channel}_{raw_id}"


def conversation_session_id(channel: str, chat_id, user_raw_id, is_private: bool) -> str:
    """
    Sessão de uma conversa de canal. Em chat privado, é a do chat ('telegram_123').
    Em grupo, cada membro tem a sua ('telegram_-100_123'): com uma sessão só para o grupo,
    o histórico de todos ficava no nome de quem falou primeiro, e o agente misturava as
    conversas de pessoas diferentes.
    """
    if is_private:
        return channel_session_id(channel, chat_id)
    return channel_session_id(channel, f"{chat_id}_{user_raw_id}")

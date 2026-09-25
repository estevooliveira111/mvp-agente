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

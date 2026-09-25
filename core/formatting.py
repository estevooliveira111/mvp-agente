"""
Limpeza da resposta final do agente.

Os canais mandam texto puro (o Telegram, por exemplo, sem parse_mode), então Markdown
aparece cru para o usuário ("**Negrito**", "* item"). O prompt já pede texto simples,
e esta limpeza cobre as vezes em que o LLM ignora o pedido.
"""
import re

_BOLD = re.compile(r"(\*\*|__)(.+?)\1", re.DOTALL)
_ITALIC = re.compile(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])")
_BULLET = re.compile(r"^(\s*)[*•+]\s+", re.MULTILINE)
_HEADING = re.compile(r"^\s{0,3}#{1,6}\s+", re.MULTILINE)
_INLINE_CODE = re.compile(r"`([^`\n]+)`")
_EXTRA_BLANK_LINES = re.compile(r"\n{3,}")


def strip_markdown(text: str) -> str:
    """Tira negrito, itálico, títulos e crases; listas com '*' viram '- '."""
    text = _BOLD.sub(r"\2", text)
    text = _BULLET.sub(r"\1- ", text)
    text = _ITALIC.sub(r"\1", text)
    text = _HEADING.sub("", text)
    text = _INLINE_CODE.sub(r"\1", text)
    text = _EXTRA_BLANK_LINES.sub("\n\n", text)
    return text.strip()

"""
Vínculo entre uma conta de canal (Telegram, Discord) e a API REST.

O usuário manda /vincular ao bot em conversa privada e recebe um código de uso único.
Com ele, chama POST /api/v1/auth/link, define uma senha e passa a entrar na API com o
próprio external_id (ex: 'telegram:123'). Receber o código no chat privado prova que a
pessoa é dona da conta, que é o que faltava para o /register poder aceitar esses IDs.
"""
import datetime
import hashlib
import secrets
from typing import Optional

from sqlalchemy.orm import Session

from database.models import AccountLinkCode, User
from database.user_repository import get_or_create_user

LINK_COMMAND = "/vincular"
LINK_CODE_TTL_MINUTES = 10
# Sem 0/O e 1/I, para não confundir na hora de digitar. 10 caracteres ≈ 50 bits.
LINK_CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
LINK_CODE_LENGTH = 10


def is_link_command(text: str) -> bool:
    """Aceita '/vincular' e a forma que o Telegram usa em grupos ('/vincular@nome_do_bot')."""
    first_word = text.strip().split(maxsplit=1)[0] if text.strip() else ""
    return first_word.split("@", 1)[0].lower() == LINK_COMMAND


def _hash_code(code: str) -> str:
    return hashlib.sha256(code.strip().upper().encode("utf-8")).hexdigest()


def create_link_code(db: Session, external_id: str) -> str:
    """Gera um código novo para o usuário. Pedir outro invalida o anterior."""
    user = get_or_create_user(db, external_id)
    db.query(AccountLinkCode).filter(AccountLinkCode.user_id == user.id).delete()

    code = "".join(secrets.choice(LINK_CODE_ALPHABET) for _ in range(LINK_CODE_LENGTH))
    db.add(
        AccountLinkCode(
            code_hash=_hash_code(code),
            user_id=user.id,
            expires_at=datetime.datetime.utcnow() + datetime.timedelta(minutes=LINK_CODE_TTL_MINUTES),
        )
    )
    db.commit()
    return code


def redeem_link_code(db: Session, code: str) -> Optional[User]:
    """Consome o código e devolve o dono. Código inválido, expirado ou já usado devolve None."""
    link = db.query(AccountLinkCode).filter(AccountLinkCode.code_hash == _hash_code(code)).first()
    if not link:
        return None

    user = link.user
    expired = link.expires_at < datetime.datetime.utcnow()
    db.delete(link)
    db.commit()
    return None if expired else user


def link_command_reply(external_id: str, is_private: bool) -> str:
    """Resposta do bot ao /vincular. Abre a própria sessão de banco (os canais não têm uma)."""
    if not is_private:
        return "Por segurança, peça o código de vínculo numa conversa privada comigo."

    from database.database import SessionLocal

    if SessionLocal is None:
        return "Não consegui gerar o código agora (banco de dados indisponível). Tente mais tarde."

    db = SessionLocal()
    try:
        code = create_link_code(db, external_id)
    finally:
        db.close()

    return (
        f"Seu código de vínculo é: {code}\n\n"
        f"Ele vale por {LINK_CODE_TTL_MINUTES} minutos e só pode ser usado uma vez. "
        "Envie-o para POST /api/v1/auth/link junto com a senha que quer usar. "
        f"Depois, entre na API com o usuário '{external_id}'.\n"
        "Não compartilhe esse código com ninguém."
    )

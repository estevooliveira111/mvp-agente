"""
Migra os IDs gravados antes de core/identity.py para o formato com prefixo de canal.

Antes, os canais gravavam:
  - Telegram: usuário '123' e sessão '<chat_id>' (ex: '123' ou '-100456' em grupos)
  - Discord:  usuário '456' e sessão 'discord_<canal>' (a sessão já estava certa)
  - CLI:      usuário 'user_terminal' e sessão 'sessao_cli_local'

Agora são 'telegram:123' / 'telegram_123', 'discord:456' e 'cli:terminal' / 'cli_local'.
Sem a migração, o histórico antigo não aparece para ninguém.

Um usuário numérico pode ser do Telegram ou do Discord; o script decide pelas sessões
dele e pula (listando no relatório) os casos que não dá para decidir. Se o ID novo já
existir, porque a pessoa voltou a falar depois da mudança, os dados são juntados.

Uso (sem --apply, só mostra o que faria):
    python -m database.migrations.prefix_channel_ids
    python -m database.migrations.prefix_channel_ids --apply
    python -m database.migrations.prefix_channel_ids --apply --drop-events
"""
import argparse
import re
from typing import List, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from core.identity import CHANNEL_ID_SEPARATOR, channel_session_id, channel_user_id
from database.models import ChatSessionDB, MessageDB, User

LEGACY_CLI_USER = "user_terminal"
LEGACY_CLI_SESSION = "sessao_cli_local"
NUMERIC_ID = re.compile(r"^-?\d+$")


def _new_session_id(old_session_id: str) -> Optional[str]:
    if old_session_id == LEGACY_CLI_SESSION:
        return channel_session_id("cli", "local")
    if NUMERIC_ID.match(old_session_id):
        return channel_session_id("telegram", old_session_id)
    # 'discord_…' já está no formato novo; sessões criadas pela API não mudam.
    return None


def _new_external_id(user: User, old_session_ids: List[str]) -> Optional[str]:
    external_id = user.external_id
    # Usuários da API (com senha) e os já migrados ficam como estão.
    if user.hashed_password or CHANNEL_ID_SEPARATOR in external_id:
        return None
    if external_id == LEGACY_CLI_USER:
        return channel_user_id("cli", "terminal")
    if not NUMERIC_ID.match(external_id) or not old_session_ids:
        return None
    if all(sid.startswith("discord_") for sid in old_session_ids):
        return channel_user_id("discord", external_id)
    if all(NUMERIC_ID.match(sid) for sid in old_session_ids):
        return channel_user_id("telegram", external_id)
    return None


def migrate(db: Session, drop_events: bool = False) -> List[str]:
    """Aplica a migração na sessão (sem commit) e devolve o relatório, uma linha por mudança."""
    report = []

    # 1. Usuários, decididos pelas sessões antigas (antes de renomeá-las).
    for user in db.query(User).order_by(User.id).all():
        old_session_ids = [s.session_id for s in user.sessions]
        new_id = _new_external_id(user, old_session_ids)
        if new_id is None:
            if NUMERIC_ID.match(user.external_id) and not user.hashed_password:
                report.append(f"PULADO usuário '{user.external_id}': canal indefinido (sessões: {old_session_ids})")
            continue

        target = db.query(User).filter(User.external_id == new_id).first()
        if target:
            # Pela relação (e não pelo user_id), para a sessão sair de user.sessions: senão
            # o delete abaixo zeraria o user_id dela.
            for session in list(user.sessions):
                session.user = target
            db.flush()
            db.delete(user)
            report.append(f"usuário '{user.external_id}' juntado a '{new_id}'")
        else:
            report.append(f"usuário '{user.external_id}' -> '{new_id}'")
            user.external_id = new_id
        db.flush()

    # 2. Sessões.
    for session in db.query(ChatSessionDB).order_by(ChatSessionDB.id).all():
        new_id = _new_session_id(session.session_id)
        if new_id is None:
            continue

        target = db.query(ChatSessionDB).filter(ChatSessionDB.session_id == new_id).first()
        if target:
            db.query(MessageDB).filter(MessageDB.session_id == session.id).update(
                {MessageDB.session_id: target.id}
            )
            db.delete(session)
            report.append(f"sessão '{session.session_id}' juntada a '{new_id}'")
        else:
            report.append(f"sessão '{session.session_id}' -> '{new_id}'")
            session.session_id = new_id
        db.flush()

    # 3. Tabela do calendário removido (o create_all não apaga tabelas).
    if drop_events:
        db.execute(text("DROP TABLE IF EXISTS events"))
        report.append("tabela 'events' removida (se existia)")

    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--apply", action="store_true", help="grava as mudanças (sem isso, só mostra)")
    parser.add_argument("--drop-events", action="store_true", help="remove a tabela 'events' do calendário antigo")
    args = parser.parse_args()

    from database.database import SessionLocal

    if SessionLocal is None:
        raise SystemExit("Banco de dados indisponível.")

    db = SessionLocal()
    try:
        report = migrate(db, drop_events=args.drop_events)
        for line in report or ["Nada para migrar."]:
            print(line)
        if args.apply:
            db.commit()
            print("\nMudanças gravadas.")
        else:
            db.rollback()
            print("\nSimulação: nada foi gravado. Rode com --apply para gravar.")
    finally:
        db.close()


if __name__ == "__main__":
    main()

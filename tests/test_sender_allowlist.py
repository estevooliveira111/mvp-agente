import json

import tools.email_sender as email_sender
import tools.telegram_sender as telegram_sender


def _allow_emails(monkeypatch, allowed):
    monkeypatch.setattr(email_sender.settings, "EMAIL_ALLOWED_RECIPIENTS", allowed)
    # Sem SMTP configurado: um destinatário liberado para no erro de credenciais, sem rede.
    monkeypatch.delenv("SMTP_USER", raising=False)
    monkeypatch.delenv("SMTP_PASS", raising=False)


def _send_email(to_email):
    return json.loads(email_sender.execute(to_email=to_email, subject="Oi", body="Teste"))


def test_email_blocked_when_allowlist_is_empty(monkeypatch):
    _allow_emails(monkeypatch, [])

    assert "não autorizado" in _send_email("alguem@exemplo.com")["message"]


def test_email_allows_listed_address_and_domain(monkeypatch):
    _allow_emails(monkeypatch, ["eu@exemplo.com", "@empresa.com"])

    assert "Credenciais SMTP" in _send_email("Eu@Exemplo.com")["message"]
    assert "Credenciais SMTP" in _send_email("qualquer@empresa.com")["message"]
    assert "não autorizado" in _send_email("outro@exemplo.com")["message"]


def test_email_blocks_if_any_recipient_is_not_allowed(monkeypatch):
    _allow_emails(monkeypatch, ["eu@exemplo.com"])

    result = _send_email("eu@exemplo.com, vitima@outro.com")

    assert "vitima@outro.com" in result["message"]


def test_email_blocks_header_injection(monkeypatch):
    _allow_emails(monkeypatch, ["eu@exemplo.com"])

    assert "não autorizado" in _send_email("eu@exemplo.com\nBcc: vitima@outro.com")["message"]


def test_telegram_blocks_chat_outside_allowlist(monkeypatch):
    monkeypatch.setattr(telegram_sender.settings, "TELEGRAM_ALLOWED_CHAT_IDS", ["123", "@MeuCanal"])
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)

    blocked = json.loads(telegram_sender.execute(chat_id="999", text="oi"))
    allowed = json.loads(telegram_sender.execute(chat_id="@meucanal", text="oi"))

    assert "não está autorizado" in blocked["message"]
    # Liberado: para na falta do token, antes de qualquer chamada de rede.
    assert "Token do Bot" in allowed["message"]

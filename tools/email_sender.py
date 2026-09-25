import json
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import getaddresses
from cryptography.fernet import Fernet
from dotenv import load_dotenv
from core.config import settings

# Carrega variáveis de ambiente (como credenciais de e-mail) do arquivo .env
load_dotenv()

# 1. Metadados: Define como a IA enxerga esta ferramenta
tool_metadata = {
    "name": "email_sender",
    "description": "Envia e-mails automatizados usando o protocolo SMTP com estruturação MIME. Permite envio de relatórios e mensagens em texto ou HTML, com opção de criptografar o conteúdo antes de enviar.",
    "parameters": {
        "type": "object",
        "properties": {
            "to_email": {
                "type": "string",
                "description": "Endereço de e-mail de destino."
            },
            "subject": {
                "type": "string",
                "description": "Assunto do e-mail."
            },
            "body": {
                "type": "string",
                "description": "Corpo da mensagem (texto simples ou HTML)."
            },
            "is_html": {
                "type": "boolean",
                "description": "(Opcional) Define se a mensagem deve ser interpretada como HTML. O padrão é texto simples (false)."
            },
            "encrypt_body": {
                "type": "boolean",
                "description": "(Opcional) Se verdadeiro, o corpo da mensagem será cifrado com Fernet, garantindo confidencialidade absoluta em trânsito."
            }
        },
        "required": ["to_email", "subject", "body"]
    }
}

def _is_allowed_recipient(address: str) -> bool:
    """Confere o endereço contra EMAIL_ALLOWED_RECIPIENTS (endereços ou '@dominio')."""
    address = address.lower()
    domain = "@" + address.rsplit("@", 1)[-1]
    allowed = [item.lower() for item in settings.EMAIL_ALLOWED_RECIPIENTS]
    return address in allowed or domain in allowed


def _blocked_recipients(to_email: str):
    """
    Devolve os destinatários fora da lista permitida. O campo pode trazer vários
    endereços separados por vírgula, e todos precisam estar liberados.
    """
    if "\r" in to_email or "\n" in to_email:
        return [to_email]
    addresses = [addr for _, addr in getaddresses([to_email]) if addr]
    if not addresses:
        return [to_email]
    return [addr for addr in addresses if "@" not in addr or not _is_allowed_recipient(addr)]


# 2. Execução: O que roda quando a IA chama a ferramenta
def execute(**kwargs):
    """
    Constrói e envia um e-mail de forma segura usando smtplib.
    Autentica via TLS no servidor definido nas variáveis de ambiente.
    """
    to_email = kwargs.get("to_email")
    subject = kwargs.get("subject")
    body = kwargs.get("body")
    is_html = kwargs.get("is_html", False)
    encrypt_body = kwargs.get("encrypt_body", False)
    
    if not all([to_email, subject, body]):
        return json.dumps({"status": "error", "message": "Os parâmetros 'to_email', 'subject' e 'body' são obrigatórios."})

    # Qualquer pessoa que fala com o bot pode pedir um e-mail: sem essa trava, o SMTP
    # do dono serviria para mandar spam ou phishing para qualquer endereço.
    blocked = _blocked_recipients(to_email)
    if blocked:
        return json.dumps({
            "status": "error",
            "message": f"Envio recusado: destinatário não autorizado ({', '.join(blocked)}). "
                       "Só é possível enviar para os endereços liberados em EMAIL_ALLOWED_RECIPIENTS."
        })
        
    try:
        # Configurações do SMTP buscando do .env para segurança
        smtp_server = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
        smtp_port = int(os.environ.get("SMTP_PORT", 587))
        smtp_user = os.environ.get("SMTP_USER")
        smtp_pass = os.environ.get("SMTP_PASS")
        
        # Validação básica de credenciais
        if not smtp_user or not smtp_pass:
            return json.dumps({
                "status": "error", 
                "message": "Credenciais SMTP ausentes. Configure 'SMTP_USER' e 'SMTP_PASS' no arquivo .env."
            })
            
        encryption_key = None
        
        # ==========================================
        # 1. SEGURANÇA E CRIPTOGRAFIA DO CORPO
        # ==========================================
        if encrypt_body:
            # Gera chave única para esta mensagem
            encryption_key = Fernet.generate_key().decode('utf-8')
            fernet = Fernet(encryption_key.encode('utf-8'))
            
            # Criptografa
            encrypted_body = fernet.encrypt(body.encode('utf-8'))
            
            # Substitui o corpo pela versão protegida
            body = (
                "🚨 MENSAGEM CRIPTOGRAFADA 🚨\n\n"
                "Este e-mail contém um laudo/relatório confidencial.\n\n"
                "Conteúdo cifrado:\n"
                f"{encrypted_body.decode('utf-8')}\n\n"
                "Para ler, utilize a ferramenta 'crypto_manager' com a chave repassada separadamente."
            )
            is_html = False # Força texto simples para evitar que HTML quebre o token Base64
            subject = f"[CONTEÚDO SENSÍVEL] {subject}"
            
        # ==========================================
        # 2. CONSTRUÇÃO DO E-MAIL (MIME)
        # ==========================================
        msg = MIMEMultipart()
        msg['From'] = smtp_user
        msg['To'] = to_email
        msg['Subject'] = subject
        
        # Define se é plain text ou html
        mime_type = "html" if is_html else "plain"
        msg.attach(MIMEText(body, mime_type))
        
        # ==========================================
        # 3. ENVIO VIA SMTP SEGURO (STARTTLS)
        # ==========================================
        server = smtplib.SMTP(smtp_server, smtp_port)
        
        # Inicia a camada de transporte segura (criptografia em trânsito)
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.send_message(msg)
        server.quit()
        
        # Prepara a resposta de sucesso para a IA
        response_data = {
            "message": f"E-mail entregue ao provedor com sucesso (Destino: {to_email}).",
            "subject_sent": subject
        }
        
        # Se foi cifrado, devolve a chave para a IA registrar/guardar
        if encrypt_body:
            response_data["encryption_key"] = encryption_key
            response_data["instructions"] = "Armazene esta chave de forma segura no registro do agente ou passe por um canal paralelo ao destinatário."
            
        return json.dumps({
            "status": "success",
            "data": response_data
        })
        
    except smtplib.SMTPAuthenticationError:
        return json.dumps({"status": "error", "message": "Falha de autenticação SMTP. Verifique as credenciais ou se o provedor bloqueou acesso (ex: App Passwords no Gmail)."})
    except Exception as e:
        return json.dumps({"status": "error", "message": f"Falha ao enviar o e-mail via provedor SMTP: {str(e)}"})

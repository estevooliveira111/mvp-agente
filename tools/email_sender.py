import json
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from cryptography.fernet import Fernet
from dotenv import load_dotenv

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

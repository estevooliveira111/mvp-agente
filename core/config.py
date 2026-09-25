import os
from dotenv import load_dotenv
from core.exceptions import ConfigurationException

# Carrega as variáveis de ambiente na inicialização do módulo Core
load_dotenv()


def _csv_env(name: str) -> list:
    """Lê uma variável no formato 'a, b, c' como lista, ignorando itens vazios."""
    return [item.strip() for item in os.getenv(name, "").split(",") if item.strip()]

class Settings:
    """
    Centraliza todas as configurações do sistema.
    Evita chamadas espalhadas de os.getenv() pelo código e garante valores padrão.
    """
    # Geral
    PROJECT_NAME = "MVP Agente"
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
    # Nível do log no console (o arquivo em logs/ sempre registra DEBUG).
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
    
    # Telegram
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
    DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN", "")
    WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")
    # Porta em que a API (app.py) escuta.
    API_PORT = int(os.getenv("API_PORT", 8080))
    # Com WEBHOOK_URL vazia, a API pergunta ao ngrok (API local dele) qual é a URL pública.
    NGROK_API_URL = os.getenv("NGROK_API_URL", "http://localhost:4040")
    # Segredo enviado ao Telegram no set_webhook e conferido em cada update recebido.
    # Fora de 'development', sem ele o endpoint /webhook/telegram recusa tudo.
    TELEGRAM_WEBHOOK_SECRET = os.getenv("TELEGRAM_WEBHOOK_SECRET", "")
    
    # Email / SMTP
    SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
    SMTP_USER = os.getenv("SMTP_USER", "")
    SMTP_PASS = os.getenv("SMTP_PASS", "")

    # Destinatários que as ferramentas de envio aceitam. Qualquer pessoa que fala com o
    # bot pode pedir um envio, então fora dessas listas nada sai. Vazia = envio desligado.
    # E-mail: endereços completos ou domínios com '@' (ex: 'eu@exemplo.com, @minhaempresa.com').
    EMAIL_ALLOWED_RECIPIENTS = _csv_env("EMAIL_ALLOWED_RECIPIENTS")
    # Telegram: chat_ids numéricos ou @usernames de canal.
    TELEGRAM_ALLOWED_CHAT_IDS = _csv_env("TELEGRAM_ALLOWED_CHAT_IDS")
    
    # AI Models
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    
    # Bancos de Dados / Infraestrutura
    POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", 5432))
    POSTGRES_USER = os.getenv("POSTGRES_USER", "admin")
    POSTGRES_DB = os.getenv("POSTGRES_DB", "mvp_agente")

    # POSTGRES_PASSWORD não tem default: se vazar para produção sem .env configurado,
    # deve falhar alto ao invés de conectar silenciosamente com uma senha fraca conhecida.
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
    if not POSTGRES_PASSWORD:
        if ENVIRONMENT == "development":
            POSTGRES_PASSWORD = "adminpassword"
        else:
            raise ConfigurationException(
                "POSTGRES_PASSWORD não foi definida no .env. "
                "Obrigatória fora do ambiente 'development'."
            )
    
    MEMCACHED_HOST = os.getenv("MEMCACHED_HOST", "localhost")
    MEMCACHED_PORT = int(os.getenv("MEMCACHED_PORT", 11211))
    
    CHROMADB_HOST = os.getenv("CHROMADB_HOST", "localhost")
    CHROMADB_PORT = int(os.getenv("CHROMADB_PORT", 8000))
    
    # Pasta única que a ferramenta file_read pode ler (relativa à raiz do projeto).
    FILE_READ_BASE_DIR = os.getenv("FILE_READ_BASE_DIR", "data/files")


    # Autenticação (JWT) das rotas REST de chat.
    # Mesma regra do POSTGRES_PASSWORD: sem valor fora de 'development', falha alto
    # em vez de assinar tokens com uma chave fraca conhecida.
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
    if not JWT_SECRET_KEY:
        if ENVIRONMENT == "development":
            JWT_SECRET_KEY = "dev-only-insecure-secret-key"
        else:
            raise ConfigurationException(
                "JWT_SECRET_KEY não foi definida no .env. "
                "Obrigatória fora do ambiente 'development'."
            )

    JWT_ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60))

# Instância Singleton global para importação em outros arquivos:
# from core.config import settings
settings = Settings()

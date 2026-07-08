import os
from dotenv import load_dotenv
from core.exceptions import ConfigurationException

# Carrega as variáveis de ambiente na inicialização do módulo Core
load_dotenv()

class Settings:
    """
    Centraliza todas as configurações do sistema.
    Evita chamadas espalhadas de os.getenv() pelo código e garante valores padrão.
    """
    # Geral
    PROJECT_NAME = "MVP Agente"
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
    
    # Telegram
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
    DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN", "")
    WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")
    
    # Email / SMTP
    SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
    SMTP_USER = os.getenv("SMTP_USER", "")
    SMTP_PASS = os.getenv("SMTP_PASS", "")
    
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
    
    # Segurança Core
    # Chave mestre (opcional) que pode ser usada no SecurityManager
    MASTER_ENCRYPTION_KEY = os.getenv("MASTER_ENCRYPTION_KEY", "")

    # CORS: origens do front-end autorizadas a chamar esta API.
    # Padrão cobre o dev server do Vite (ui/). Em produção, defina via .env.
    CORS_ORIGINS = [
        origin.strip()
        for origin in os.getenv(
            "CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
        ).split(",")
        if origin.strip()
    ]

# Instância Singleton global para importação em outros arquivos:
# from core.config import settings
settings = Settings()

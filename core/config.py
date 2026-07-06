import os
from dotenv import load_dotenv

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
    
    # Email / SMTP
    SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
    SMTP_USER = os.getenv("SMTP_USER", "")
    SMTP_PASS = os.getenv("SMTP_PASS", "")
    
    # AI Models
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    
    # Bancos de Dados / Infraestrutura
    POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", 5432))
    POSTGRES_USER = os.getenv("POSTGRES_USER", "admin")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "adminpassword")
    POSTGRES_DB = os.getenv("POSTGRES_DB", "mvp_agente")
    
    MEMCACHED_HOST = os.getenv("MEMCACHED_HOST", "localhost")
    MEMCACHED_PORT = int(os.getenv("MEMCACHED_PORT", 11211))
    
    CHROMADB_HOST = os.getenv("CHROMADB_HOST", "localhost")
    CHROMADB_PORT = int(os.getenv("CHROMADB_PORT", 8000))
    
    # Segurança Core
    # Chave mestre (opcional) que pode ser usada no SecurityManager
    MASTER_ENCRYPTION_KEY = os.getenv("MASTER_ENCRYPTION_KEY", "")

# Instância Singleton global para importação em outros arquivos:
# from core.config import settings
settings = Settings()

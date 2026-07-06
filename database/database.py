from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from core.config import settings
from core.logger import logger

# Construção da Connection String do PostgreSQL (Driver psycopg2)
# Ex: postgresql://admin:adminpassword@localhost:5432/mvp_agente
DATABASE_URL = f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"

try:
    # Cria o motor (engine) de conexão ao Banco Relacional
    engine = create_engine(DATABASE_URL, echo=False)
    
    # Fábrica de Sessões para abrir e fechar as transações
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Classe base que todos os modelos de tabelas (models.py) herdarão
    Base = declarative_base()
    
    logger.info("Configuração do SQLAlchemy (Módulo Database) inicializada.")
    
except Exception as e:
    logger.error(f"Falha ao configurar a conexão com o PostgreSQL: {e}")
    engine = None
    SessionLocal = None
    Base = None

def get_db():
    """
    Generator injetável para prover uma sessão do banco de dados relacional.
    Uso: Onde precisar de banco, chame a função, e ela abrirá e fechará a conexão com segurança (yield).
    """
    if not SessionLocal:
        logger.error("Tentativa de uso do DB com SessionLocal inválido/caído.")
        yield None
        return
        
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

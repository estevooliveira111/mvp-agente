from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from core.config import settings

engine = create_engine(
    settings.get_database_url,
    # connect_args={"check_same_thread": False} if settings.DATABASE_PROVIDER == "sqlite" else {}
    connect_args={"check_same_thread": False} if "sqlite" in settings.get_database_url else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

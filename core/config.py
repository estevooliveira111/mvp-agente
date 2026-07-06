from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal, Optional

class Settings(BaseSettings):
    DATABASE_PROVIDER: Literal["sqlite", "mysql"] = "sqlite"
    
    # Used for specific override, otherwise constructed from provider
    DATABASE_URL: Optional[str] = None
    
    JWT_SECRET: str
    JWT_EXPIRATION_MINUTES: int = 60
    
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    ENVIRONMENT: Literal["development", "production"] = "development"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def get_database_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        if self.DATABASE_PROVIDER == "sqlite":
            return "sqlite:///./app.db"
        elif self.DATABASE_PROVIDER == "mysql":
            # Default fallback for mysql if not provided, but usually it should be provided
            return "mysql+pymysql://root:password@localhost/appdb"
        return "sqlite:///./app.db"

settings = Settings()

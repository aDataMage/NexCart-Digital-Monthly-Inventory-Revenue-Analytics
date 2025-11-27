from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Database
    DB_URL: str = "sqlite:///./inventory_v2.db"

    # LLM Provider
    LLM_API_KEY: Optional[str] = 'API_KEY'
    LLM_MODEL: str = "Model"

    # Email
    SMTP_SERVER: str = "host"
    SMTP_PORT: int = port
    SMTP_USER: Optional[str] = ""
    SMTP_PASSWORD: Optional[str] = ""
    EMAIL_FROM: str = ""
    EMAIL_TO: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()

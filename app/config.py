from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
import os

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # LiteLLM Configuration (Hard Rule 1, 2, 8)
    LLM_MODEL: str = "gemini/gemini-3.5-flash-lite"
    LLM_API_KEY: str = ""
    LLM_API_BASE: Optional[str] = None
    EMBEDDING_MODEL: Optional[str] = "text-embedding-3-small"
    LITELLM_LOCAL_MODEL_COST_MAP: bool = True
    LITELLM_TELEMETRY: bool = False

    # Database Configuration (Hard Rule 4, 7)
    DATABASE_URL: str = "postgresql+psycopg://ebuddy_user:ebuddy_password@db:5432/ebuddy"
    LOCAL_DATABASE_URL: Optional[str] = "postgresql+psycopg://ebuddy_user:ebuddy_password@localhost:5432/ebuddy"

    # Application Settings
    APP_ENV: str = "production"
    APP_PORT: int = 8000
    ADMINER_PORT: int = 8080
    LOG_LEVEL: str = "INFO"

    @property
    def effective_db_url(self) -> str:
        # If running locally outside docker and DB host is 'db', fallback to localhost
        url = self.DATABASE_URL
        if "@db:" in url and not os.path.exists("/.dockerenv"):
            if self.LOCAL_DATABASE_URL:
                return self.LOCAL_DATABASE_URL
            return url.replace("@db:", "@localhost:")
        return url

settings = Settings()

# Enforce LiteLLM offline safety flags immediately
os.environ["LITELLM_LOCAL_MODEL_COST_MAP"] = str(settings.LITELLM_LOCAL_MODEL_COST_MAP)
os.environ["LITELLM_TELEMETRY"] = str(settings.LITELLM_TELEMETRY)


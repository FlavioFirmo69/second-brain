from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Second Brain"
    app_env: str = "development"
    app_host: str = "127.0.0.1"
    app_port: int = 8000
    app_timezone: str = "Europe/Rome"
    frontend_origins: str = "http://localhost:5173"

    database_url: str = ""

    default_user_email: str = "owner@secondbrain.local"

    llm_enabled: bool = False
    llm_base_url: str = "https://api.openai.com/v1"
    llm_api_key: str = ""
    llm_model: str = ""

    @property
    def cors_origins(self) -> list[str]:
        return [value.strip() for value in self.frontend_origins.split(",") if value.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()

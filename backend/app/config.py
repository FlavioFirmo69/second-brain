from functools import lru_cache
from urllib.parse import quote_plus

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Second Brain"
    app_env: str = "development"
    app_host: str = "127.0.0.1"
    app_port: int = 8000
    app_timezone: str = "Europe/Rome"
    frontend_origins: str = "http://localhost:5173"

    db_server: str = ""
    db_name: str = ""
    db_user: str = ""
    db_password: str = ""
    db_driver: str = "ODBC Driver 18 for SQL Server"
    db_encrypt: str = "yes"
    db_trust_server_certificate: str = "no"
    database_url_override: str | None = None

    default_user_email: str = "owner@secondbrain.local"

    llm_enabled: bool = False
    llm_base_url: str = "https://api.openai.com/v1"
    llm_api_key: str = ""
    llm_model: str = ""

    @property
    def database_url(self) -> str:
        if self.database_url_override:
            return self.database_url_override
        missing = [name for name in ("db_server", "db_name", "db_user", "db_password") if not getattr(self, name)]
        if missing:
            raise RuntimeError(f"Configurazione database incompleta: {', '.join(missing)}")
        odbc = (
            f"DRIVER={{{self.db_driver}}};SERVER={self.db_server};DATABASE={self.db_name};"
            f"UID={self.db_user};PWD={self.db_password};Encrypt={self.db_encrypt};"
            f"TrustServerCertificate={self.db_trust_server_certificate};"
        )
        return f"mssql+pyodbc:///?odbc_connect={quote_plus(odbc)}"

    @property
    def cors_origins(self) -> list[str]:
        return [value.strip() for value in self.frontend_origins.split(",") if value.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application
    app_name: str = "OnBxrd API"
    app_env: Literal["development", "production", "test"] = "development"
    app_port: int = Field(default=8000, ge=1, le=65535)
    app_host: str = "0.0.0.0"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    cors_origins: str = "http://localhost:3000,http://localhost:5173"

    # Local authentication adapter. Replace this with JWT/OIDC before production.
    dev_auth_enabled: bool = True

    # LLM
    openai_api_key: str = ""
    model_name: str = "gpt-4o-mini"
    llm_temperature: float = Field(default=0.1, ge=0.0, le=2.0)

    # Database
    database_url: str = "sqlite+aiosqlite:///./data/app.db"
    database_echo: bool = False
    auto_create_tables: bool = True

    # Knowledge base
    knowledge_storage_dir: Path = Path("./data/handbooks")
    max_upload_bytes: int = Field(default=20 * 1024 * 1024, gt=0)
    embedding_dimensions: int = Field(default=1536, gt=0)

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()

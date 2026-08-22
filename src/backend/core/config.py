from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, model_validator
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

    # Legacy local headers are disabled by default. Bearer JWT is the primary adapter.
    dev_auth_enabled: bool = False

    # Authentication
    jwt_secret_key: str = "local-development-secret-change-before-deploying"
    jwt_algorithm: Literal["HS256"] = "HS256"
    jwt_issuer: str = "onbxrd-api"
    jwt_audience: str = "onbxrd-clients"
    jwt_access_token_minutes: int = Field(default=15, ge=1, le=1440)
    jwt_refresh_token_days: int = Field(default=30, ge=1, le=365)
    auth_max_failed_attempts: int = Field(default=5, ge=1, le=20)
    auth_lockout_minutes: int = Field(default=15, ge=1, le=1440)
    management_bootstrap_token: str = ""
    password_reset_token_minutes: int = Field(default=15, ge=5, le=60)
    password_reset_url_base: str = "http://localhost:3000/reset-password"
    email_verification_token_minutes: int = Field(default=10, ge=5, le=60)
    email_verification_max_attempts: int = Field(default=5, ge=1, le=10)
    email_verification_resend_cooldown_seconds: int = Field(default=60, ge=1, le=3600)
    email_verification_max_sends: int = Field(default=3, ge=1, le=10)
    email_verification_max_ip_sends: int = Field(default=10, ge=1, le=100)
    email_verification_window_minutes: int = Field(default=15, ge=1, le=1440)

    # Email delivery. An empty SMTP host keeps local development functional; the
    # reset endpoint still returns a non-enumerating response in that mode.
    smtp_host: str = ""
    smtp_port: int = Field(default=587, ge=1, le=65535)
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from_email: str = ""
    smtp_use_tls: bool = True

    # Private S3 attachment storage.
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_region: str = ""
    aws_s3_bucket_name: str = ""
    aws_s3_endpoint_url: str = ""
    s3_presigned_url_expire_seconds: int = Field(default=900, ge=60, le=86400)
    attachment_allowed_mime_types: str = (
        "application/pdf,image/jpeg,image/png,image/webp,text/plain,"
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )

    # LLM
    openai_api_key: str = ""
    # Legacy Qwen/DashScope and vector-store settings remain available for the
    # original LangGraph/RAG adapter while the modular backend uses the same
    # settings object.
    qwen_api_key: str = ""
    qwen_api_base: str = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
    openai_api_base: str = "https://api.openai.com/v1"
    model_name: str = "gpt-4o-mini"
    qwen_model_name: str = "qwen3.5-plus"
    groq_api_key: str = ""
    groq_api_base: str = "https://api.groq.com/openai/v1"
    groq_model_name: str = "llama-3.3-70b-versatile"
    embedding_model_name: str = "text-embedding-v4"
    llm_temperature: float = Field(default=0.1, ge=0.0, le=2.0)

    # Database
    database_url: str = "sqlite+aiosqlite:///./data/app.db"
    database_echo: bool = False
    auto_create_tables: bool = True

    # Knowledge base
    knowledge_storage_dir: Path = Path("./data/handbooks")
    # Temporary local handbook context used before the production retriever is ready.
    # Set to an empty value to disable the file fallback.
    handbook_context_file: str = "./data/handbook1.md"
    handbook_chunk_max_chars: int = Field(default=4500, ge=1000, le=12000)
    handbook_context_top_k: int = Field(default=5, ge=1, le=10)
    handbook_context_min_score: float = Field(default=1.5, ge=0.0, le=100.0)
    chroma_persist_dir: str = "./data/chroma"
    chroma_server_host: str = ""
    chroma_server_port: int = Field(default=8000, ge=1, le=65535)
    chroma_server_ssl: bool = False
    max_upload_bytes: int = Field(default=20 * 1024 * 1024, gt=0)
    embedding_dimensions: int = Field(default=1536, gt=0)

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def allowed_attachment_mime_types(self) -> set[str]:
        return {mime.strip().lower() for mime in self.attachment_allowed_mime_types.split(",") if mime.strip()}

    @model_validator(mode="after")
    def validate_production_security(self) -> "Settings":
        if self.app_env == "production":
            if self.dev_auth_enabled:
                raise ValueError("DEV_AUTH_ENABLED must be false in production")
            insecure_secret = self.jwt_secret_key.startswith(("local-development", "replace-with"))
            if len(self.jwt_secret_key) < 32 or insecure_secret:
                raise ValueError("JWT_SECRET_KEY must be a unique secret of at least 32 characters")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()

"""Application settings loaded from environment / .env."""

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Strongly-typed settings, loaded once."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # LLM
    llm_provider: Literal["openai", "anthropic", "google", "mistral"] = "mistral"
    llm_model: str = "mistral-small-latest"
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    google_api_key: str | None = None
    mistral_api_key: str | None = None

    # Embeddings — can target a different provider than the LLM if desired.
    embedding_provider: Literal["openai", "google", "mistral"] = "mistral"
    embedding_model: str = "mistral-embed"
    embedding_dim: int = 1024

    # Postgres — set DATABASE_URL to override the discrete fields.
    # Accepts either ``postgresql://`` or ``postgresql+asyncpg://`` schemes.
    database_url: str | None = None
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_user: str = "memora"
    postgres_password: str = "memora"
    postgres_db: str = "memora"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Whisper — tiny.en fits Render's 512MB free tier; bump for better quality on bigger hosts.
    whisper_model: str = "tiny.en"
    whisper_device: Literal["cpu", "cuda"] = "cpu"
    whisper_compute_type: str = "int8"

    # Server
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: str = "http://localhost:3000"

    # Agent
    short_term_window: int = 10
    long_term_top_k: int = 8

    @property
    def postgres_dsn(self) -> str:
        if self.database_url:
            # Normalize scheme for SQLAlchemy async driver.
            url = self.database_url
            if url.startswith("postgresql://"):
                url = "postgresql+asyncpg://" + url[len("postgresql://") :]
            elif url.startswith("postgres://"):
                url = "postgresql+asyncpg://" + url[len("postgres://") :]
            return url
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()

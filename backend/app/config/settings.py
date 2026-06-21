from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.config.paths import BACKEND_ROOT, DATA_PATH


class Settings(BaseSettings):
    """Runtime configuration loaded from environment variables or backend/.env."""

    model_config = SettingsConfigDict(
        env_file=BACKEND_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Benefits Readiness Navigator"
    environment: str = "development"
    log_level: str = "INFO"
    database_url: str = Field(
        default="postgresql+psycopg://postgres:postgres@localhost:5432/benefits_readiness"
    )
    upload_path: Path = Field(default=BACKEND_ROOT / "uploads")
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-2.5-flash"
    gemini_timeout_seconds: float = 30.0
    use_gemini_extractor: bool = False
    max_upload_bytes: int = Field(default=10 * 1024 * 1024, ge=1)
    chroma_path: Path = Field(default=BACKEND_ROOT / "chroma_data")
    rag_min_relevance: float = Field(default=0.35, ge=0, le=1)
    rag_top_n: int = Field(default=3, ge=1, le=10)

    @property
    def data_path(self) -> Path:
        return DATA_PATH


@lru_cache
def get_settings() -> Settings:
    return Settings()

"""Application configuration via environment variables."""

from pathlib import Path
from typing import Literal

from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # API Authentication
    api_key: SecretStr

    # Notes Path
    notes_path: Path

    # Server
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    frontend_url: str = "http://localhost:5173"

    # LLM Providers
    openai_api_key: SecretStr | None = None
    azure_openai_api_key: SecretStr | None = None
    azure_openai_endpoint: str | None = None
    azure_openai_deployment: str | None = None
    anthropic_api_key: SecretStr | None = None
    openrouter_api_key: SecretStr | None = None

    # Model Routing
    simple_query_provider: Literal["openai", "azure_openai", "anthropic", "openrouter"] = "openai"
    simple_query_model: str = "gpt-4o-mini"
    complex_query_provider: Literal["openai", "azure_openai", "anthropic", "openrouter"] = (
        "anthropic"
    )
    complex_query_model: str = "claude-3-5-sonnet-20241022"

    # Embeddings
    embedding_provider: Literal["openai", "azure_openai"] = "openai"
    embedding_model: str = "text-embedding-3-small"

    # Storage
    chroma_persist_path: Path = Path("./data/chroma")
    sqlite_path: Path = Path("./data/index.db")
    costs_path: Path = Path("./data/costs.json")

    @field_validator("notes_path")
    @classmethod
    def validate_notes_path(cls, v: Path) -> Path:
        """Ensure notes path exists."""
        if not v.exists():
            raise ValueError(f"Notes path does not exist: {v}")
        if not v.is_dir():
            raise ValueError(f"Notes path is not a directory: {v}")
        return v

    @field_validator("chroma_persist_path", "sqlite_path", "costs_path")
    @classmethod
    def ensure_parent_exists(cls, v: Path) -> Path:
        """Create parent directory if it doesn't exist."""
        v.parent.mkdir(parents=True, exist_ok=True)
        return v

    def get_configured_providers(self) -> list[str]:
        """Return list of providers that have API keys configured."""
        providers = []
        if self.openai_api_key:
            providers.append("openai")
        if self.azure_openai_api_key and self.azure_openai_endpoint:
            providers.append("azure_openai")
        if self.anthropic_api_key:
            providers.append("anthropic")
        if self.openrouter_api_key:
            providers.append("openrouter")
        return providers


def get_settings() -> Settings:
    """Get application settings (cached)."""
    return Settings()  # type: ignore[call-arg]

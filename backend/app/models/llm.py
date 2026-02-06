"""LLM-related Pydantic models."""

from enum import Enum

from pydantic import BaseModel, SecretStr


class LLMProvider(str, Enum):
    """Supported LLM providers."""

    OPENAI = "openai"
    AZURE_OPENAI = "azure_openai"
    ANTHROPIC = "anthropic"
    OPENROUTER = "openrouter"


class TokenUsage(BaseModel):
    """Token usage statistics from an LLM call."""

    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class LLMConfig(BaseModel):
    """Configuration for an LLM provider."""

    provider: LLMProvider
    model: str
    api_key: SecretStr

    # Provider-specific settings
    azure_endpoint: str | None = None
    azure_deployment: str | None = None
    azure_api_version: str = "2024-02-01"
    openrouter_site_url: str | None = None
    openrouter_app_name: str = "obsidian-ai"


class LLMResponse(BaseModel):
    """Standardized response from any LLM provider."""

    content: str
    model: str
    provider: LLMProvider
    usage: TokenUsage
    latency_ms: int

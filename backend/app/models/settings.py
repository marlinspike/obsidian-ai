"""Settings-related Pydantic models."""

from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.llm import LLMProvider


class ModelConfig(BaseModel):
    """User-configurable model settings."""

    simple_query_provider: LLMProvider
    simple_query_model: str
    complex_query_provider: LLMProvider
    complex_query_model: str
    embedding_provider: LLMProvider
    embedding_model: str


class AvailableModel(BaseModel):
    """A model available for selection."""

    provider: LLMProvider
    model: str
    display_name: str
    input_price_per_million: Decimal = Field(decimal_places=6)
    output_price_per_million: Decimal = Field(decimal_places=6)
    is_configured: bool  # Whether API key is set for this provider
    is_embedding_model: bool = False


class ProviderStatus(BaseModel):
    """Status of a provider."""

    provider: LLMProvider
    display_name: str
    is_configured: bool
    available_models: list[str]

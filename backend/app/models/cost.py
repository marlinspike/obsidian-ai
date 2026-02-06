"""Cost tracking Pydantic models."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.llm import LLMProvider


class ModelPricing(BaseModel):
    """Pricing per 1M tokens for a model."""

    model: str
    provider: LLMProvider
    display_name: str
    input_price_per_million: Decimal = Field(decimal_places=6)
    output_price_per_million: Decimal = Field(decimal_places=6)
    embedding_price_per_million: Decimal | None = Field(default=None, decimal_places=6)


# Pre-configured pricing table (as of late 2024)
DEFAULT_PRICING: dict[str, ModelPricing] = {
    # OpenAI
    "gpt-4o": ModelPricing(
        model="gpt-4o",
        provider=LLMProvider.OPENAI,
        display_name="GPT-4o",
        input_price_per_million=Decimal("2.50"),
        output_price_per_million=Decimal("10.00"),
    ),
    "gpt-4o-mini": ModelPricing(
        model="gpt-4o-mini",
        provider=LLMProvider.OPENAI,
        display_name="GPT-4o Mini",
        input_price_per_million=Decimal("0.15"),
        output_price_per_million=Decimal("0.60"),
    ),
    "gpt-4-turbo": ModelPricing(
        model="gpt-4-turbo",
        provider=LLMProvider.OPENAI,
        display_name="GPT-4 Turbo",
        input_price_per_million=Decimal("10.00"),
        output_price_per_million=Decimal("30.00"),
    ),
    "text-embedding-3-small": ModelPricing(
        model="text-embedding-3-small",
        provider=LLMProvider.OPENAI,
        display_name="Embedding 3 Small",
        input_price_per_million=Decimal("0.02"),
        output_price_per_million=Decimal("0.00"),
        embedding_price_per_million=Decimal("0.02"),
    ),
    "text-embedding-3-large": ModelPricing(
        model="text-embedding-3-large",
        provider=LLMProvider.OPENAI,
        display_name="Embedding 3 Large",
        input_price_per_million=Decimal("0.13"),
        output_price_per_million=Decimal("0.00"),
        embedding_price_per_million=Decimal("0.13"),
    ),
    # Anthropic
    "claude-3-5-sonnet-20241022": ModelPricing(
        model="claude-3-5-sonnet-20241022",
        provider=LLMProvider.ANTHROPIC,
        display_name="Claude 3.5 Sonnet",
        input_price_per_million=Decimal("3.00"),
        output_price_per_million=Decimal("15.00"),
    ),
    "claude-3-5-haiku-20241022": ModelPricing(
        model="claude-3-5-haiku-20241022",
        provider=LLMProvider.ANTHROPIC,
        display_name="Claude 3.5 Haiku",
        input_price_per_million=Decimal("0.80"),
        output_price_per_million=Decimal("4.00"),
    ),
    "claude-3-opus-20240229": ModelPricing(
        model="claude-3-opus-20240229",
        provider=LLMProvider.ANTHROPIC,
        display_name="Claude 3 Opus",
        input_price_per_million=Decimal("15.00"),
        output_price_per_million=Decimal("75.00"),
    ),
    # Azure OpenAI (typically same pricing as OpenAI)
    "azure-gpt-4o": ModelPricing(
        model="azure-gpt-4o",
        provider=LLMProvider.AZURE_OPENAI,
        display_name="Azure GPT-4o",
        input_price_per_million=Decimal("2.50"),
        output_price_per_million=Decimal("10.00"),
    ),
    "azure-gpt-4o-mini": ModelPricing(
        model="azure-gpt-4o-mini",
        provider=LLMProvider.AZURE_OPENAI,
        display_name="Azure GPT-4o Mini",
        input_price_per_million=Decimal("0.15"),
        output_price_per_million=Decimal("0.60"),
    ),
}


class QueryCost(BaseModel):
    """Cost breakdown for a single query."""

    query_id: str
    timestamp: datetime
    model: str
    provider: LLMProvider
    input_tokens: int
    output_tokens: int
    input_cost: Decimal = Field(decimal_places=6)
    output_cost: Decimal = Field(decimal_places=6)
    total_cost: Decimal = Field(decimal_places=6)
    embedding_tokens: int | None = None
    embedding_cost: Decimal | None = Field(default=None, decimal_places=6)


class ModelCostBreakdown(BaseModel):
    """Cost breakdown for a specific model within a session."""

    model: str
    provider: LLMProvider
    query_count: int
    input_tokens: int
    output_tokens: int
    total_cost: Decimal = Field(decimal_places=6)


class CostSummary(BaseModel):
    """Cumulative cost tracking with detailed breakdowns."""

    session_id: str
    session_start: datetime
    total_queries: int
    total_cost: Decimal = Field(decimal_places=6)

    # Breakdown by model
    cost_by_model: dict[str, ModelCostBreakdown]

    # Breakdown by provider
    cost_by_provider: dict[str, Decimal]

    # Token usage
    total_input_tokens: int
    total_output_tokens: int
    total_embedding_tokens: int

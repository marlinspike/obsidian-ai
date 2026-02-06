"""Settings endpoints."""

from fastapi import APIRouter

from app.api.deps import ApiKeyDep, SettingsDep
from app.models.cost import DEFAULT_PRICING
from app.models.llm import LLMProvider
from app.models.settings import AvailableModel, ModelConfig, ProviderStatus

router = APIRouter()


@router.get("/models", response_model=list[AvailableModel])
async def get_available_models(
    _: ApiKeyDep,
    settings: SettingsDep,
) -> list[AvailableModel]:
    """Get all available models with pricing and configuration status.

    Returns:
        List of models with their pricing and whether they're configured
    """
    configured_providers = settings.get_configured_providers()

    models: list[AvailableModel] = []
    for model_name, pricing in DEFAULT_PRICING.items():
        is_embedding = pricing.embedding_price_per_million is not None

        models.append(
            AvailableModel(
                provider=pricing.provider,
                model=pricing.model,
                display_name=pricing.display_name,
                input_price_per_million=pricing.input_price_per_million,
                output_price_per_million=pricing.output_price_per_million,
                is_configured=pricing.provider.value in configured_providers,
                is_embedding_model=is_embedding,
            )
        )

    return models


@router.get("/models/current", response_model=ModelConfig)
async def get_current_model_config(
    _: ApiKeyDep,
    settings: SettingsDep,
) -> ModelConfig:
    """Get the current model configuration.

    Returns:
        Current model settings for simple/complex queries and embeddings
    """
    return ModelConfig(
        simple_query_provider=LLMProvider(settings.simple_query_provider),
        simple_query_model=settings.simple_query_model,
        complex_query_provider=LLMProvider(settings.complex_query_provider),
        complex_query_model=settings.complex_query_model,
        embedding_provider=LLMProvider(settings.embedding_provider),
        embedding_model=settings.embedding_model,
    )


@router.get("/providers", response_model=list[ProviderStatus])
async def get_providers(
    _: ApiKeyDep,
    settings: SettingsDep,
) -> list[ProviderStatus]:
    """Get status of all providers.

    Returns:
        List of providers with configuration status
    """
    configured = settings.get_configured_providers()

    # Map providers to their display names and available models
    provider_info = {
        LLMProvider.OPENAI: {
            "display_name": "OpenAI",
            "models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "text-embedding-3-small", "text-embedding-3-large"],
        },
        LLMProvider.ANTHROPIC: {
            "display_name": "Anthropic",
            "models": ["claude-3-5-sonnet-20241022", "claude-3-5-haiku-20241022", "claude-3-opus-20240229"],
        },
        LLMProvider.AZURE_OPENAI: {
            "display_name": "Azure OpenAI",
            "models": ["azure-gpt-4o", "azure-gpt-4o-mini"],
        },
        LLMProvider.OPENROUTER: {
            "display_name": "OpenRouter",
            "models": ["openai/gpt-4o", "anthropic/claude-3.5-sonnet", "meta-llama/llama-3.1-70b-instruct"],
        },
    }

    return [
        ProviderStatus(
            provider=provider,
            display_name=info["display_name"],
            is_configured=provider.value in configured,
            available_models=info["models"],
        )
        for provider, info in provider_info.items()
    ]

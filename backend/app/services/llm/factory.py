"""Factory for creating LLM providers."""

from app.config import Settings
from app.core.exceptions import ProviderNotConfiguredError
from app.models.llm import LLMProvider
from app.services.llm.anthropic_provider import AnthropicProvider
from app.services.llm.azure_openai_provider import AzureOpenAIProvider
from app.services.llm.base import BaseLLMProvider
from app.services.llm.openai_provider import OpenAIProvider
from app.services.llm.openrouter_provider import OpenRouterProvider


class LLMProviderFactory:
    """Factory for creating LLM provider instances."""

    def __init__(self, settings: Settings):
        """Initialize factory with settings.

        Args:
            settings: Application settings
        """
        self.settings = settings
        self._providers: dict[str, BaseLLMProvider] = {}

    def get_provider(
        self,
        provider: LLMProvider | str,
        model: str | None = None,
    ) -> BaseLLMProvider:
        """Get or create an LLM provider instance.

        Args:
            provider: Provider type
            model: Model to use (optional, uses default if not specified)

        Returns:
            LLM provider instance

        Raises:
            ProviderNotConfiguredError: If provider API key is not configured
        """
        if isinstance(provider, str):
            provider = LLMProvider(provider)

        # Use model as cache key
        cache_key = f"{provider.value}:{model or 'default'}"

        if cache_key in self._providers:
            return self._providers[cache_key]

        instance = self._create_provider(provider, model)
        self._providers[cache_key] = instance
        return instance

    def _create_provider(
        self,
        provider: LLMProvider,
        model: str | None,
    ) -> BaseLLMProvider:
        """Create a new provider instance.

        Args:
            provider: Provider type
            model: Model to use

        Returns:
            New provider instance
        """
        if provider == LLMProvider.OPENAI:
            if not self.settings.openai_api_key:
                raise ProviderNotConfiguredError("openai")
            return OpenAIProvider(
                api_key=self.settings.openai_api_key.get_secret_value(),
                model=model or "gpt-4o-mini",
                embedding_model=self.settings.embedding_model,
            )

        elif provider == LLMProvider.ANTHROPIC:
            if not self.settings.anthropic_api_key:
                raise ProviderNotConfiguredError("anthropic")
            return AnthropicProvider(
                api_key=self.settings.anthropic_api_key.get_secret_value(),
                model=model or "claude-3-5-sonnet-20241022",
            )

        elif provider == LLMProvider.AZURE_OPENAI:
            if (
                not self.settings.azure_openai_api_key
                or not self.settings.azure_openai_endpoint
                or not self.settings.azure_openai_deployment
            ):
                raise ProviderNotConfiguredError("azure_openai")
            return AzureOpenAIProvider(
                api_key=self.settings.azure_openai_api_key.get_secret_value(),
                endpoint=self.settings.azure_openai_endpoint,
                deployment=model or self.settings.azure_openai_deployment,
            )

        elif provider == LLMProvider.OPENROUTER:
            if not self.settings.openrouter_api_key:
                raise ProviderNotConfiguredError("openrouter")
            return OpenRouterProvider(
                api_key=self.settings.openrouter_api_key.get_secret_value(),
                model=model or "openai/gpt-4o-mini",
            )

        else:
            raise ValueError(f"Unknown provider: {provider}")

    def get_embedding_provider(self) -> BaseLLMProvider:
        """Get the configured embedding provider.

        Returns:
            Provider instance for embeddings
        """
        return self.get_provider(
            LLMProvider(self.settings.embedding_provider),
            self.settings.embedding_model,
        )

    def get_simple_query_provider(self) -> BaseLLMProvider:
        """Get the configured simple query provider.

        Returns:
            Provider instance for simple queries
        """
        return self.get_provider(
            LLMProvider(self.settings.simple_query_provider),
            self.settings.simple_query_model,
        )

    def get_complex_query_provider(self) -> BaseLLMProvider:
        """Get the configured complex query provider.

        Returns:
            Provider instance for complex queries
        """
        return self.get_provider(
            LLMProvider(self.settings.complex_query_provider),
            self.settings.complex_query_model,
        )

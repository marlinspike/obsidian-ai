"""Abstract base class for LLM providers."""

from abc import ABC, abstractmethod
from typing import AsyncIterator

from app.models.llm import LLMProvider, LLMResponse, TokenUsage


class BaseLLMProvider(ABC):
    """Abstract base class for all LLM providers."""

    provider: LLMProvider
    model: str

    @abstractmethod
    async def complete(
        self,
        prompt: str,
        system_prompt: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> LLMResponse:
        """Generate a completion for the given prompt.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature

        Returns:
            LLMResponse with generated content and metadata
        """
        pass

    @abstractmethod
    async def stream(
        self,
        prompt: str,
        system_prompt: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> AsyncIterator[tuple[str, TokenUsage | None]]:
        """Stream a completion for the given prompt.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature

        Yields:
            Tuples of (content_chunk, final_usage_or_none)
            Usage is only provided in the final chunk
        """
        pass

    @abstractmethod
    async def embed(self, texts: list[str]) -> tuple[list[list[float]], int]:
        """Generate embeddings for texts.

        Args:
            texts: List of texts to embed

        Returns:
            Tuple of (embeddings, total_tokens_used)
        """
        pass

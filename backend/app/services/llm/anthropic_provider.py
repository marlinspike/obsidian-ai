"""Anthropic Claude LLM provider implementation."""

import time
from typing import AsyncIterator

from anthropic import AsyncAnthropic

from app.core.exceptions import LLMError
from app.models.llm import LLMProvider, LLMResponse, TokenUsage
from app.services.llm.base import BaseLLMProvider


class AnthropicProvider(BaseLLMProvider):
    """Anthropic Claude API provider."""

    provider = LLMProvider.ANTHROPIC

    def __init__(self, api_key: str, model: str = "claude-3-5-sonnet-20241022"):
        """Initialize Anthropic provider.

        Args:
            api_key: Anthropic API key
            model: Model to use
        """
        self.model = model
        self.client = AsyncAnthropic(api_key=api_key)

    async def complete(
        self,
        prompt: str,
        system_prompt: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> LLMResponse:
        """Generate a completion using Anthropic Claude.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature

        Returns:
            LLMResponse with generated content
        """
        start_time = time.time()

        try:
            kwargs: dict[str, object] = {
                "model": self.model,
                "max_tokens": max_tokens,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": temperature,
            }
            if system_prompt:
                kwargs["system"] = system_prompt

            response = await self.client.messages.create(**kwargs)  # type: ignore[arg-type]
        except Exception as e:
            raise LLMError("anthropic", str(e)) from e

        latency_ms = int((time.time() - start_time) * 1000)

        # Extract text content
        content = ""
        for block in response.content:
            if block.type == "text":
                content += block.text

        return LLMResponse(
            content=content,
            model=self.model,
            provider=self.provider,
            usage=TokenUsage(
                prompt_tokens=response.usage.input_tokens,
                completion_tokens=response.usage.output_tokens,
                total_tokens=response.usage.input_tokens + response.usage.output_tokens,
            ),
            latency_ms=latency_ms,
        )

    async def stream(
        self,
        prompt: str,
        system_prompt: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> AsyncIterator[tuple[str, TokenUsage | None]]:
        """Stream a completion using Anthropic Claude.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature

        Yields:
            Content chunks and final usage
        """
        try:
            kwargs: dict[str, object] = {
                "model": self.model,
                "max_tokens": max_tokens,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": temperature,
            }
            if system_prompt:
                kwargs["system"] = system_prompt

            async with self.client.messages.stream(**kwargs) as stream:  # type: ignore[arg-type]
                async for text in stream.text_stream:
                    yield (text, None)

                # Get final message for usage
                final_message = await stream.get_final_message()
                yield (
                    "",
                    TokenUsage(
                        prompt_tokens=final_message.usage.input_tokens,
                        completion_tokens=final_message.usage.output_tokens,
                        total_tokens=(
                            final_message.usage.input_tokens + final_message.usage.output_tokens
                        ),
                    ),
                )

        except Exception as e:
            raise LLMError("anthropic", str(e)) from e

    async def embed(self, texts: list[str]) -> tuple[list[list[float]], int]:
        """Generate embeddings.

        Note: Anthropic doesn't provide an embedding API,
        so this falls back to raising an error.

        Args:
            texts: List of texts to embed

        Raises:
            LLMError: Anthropic doesn't support embeddings
        """
        raise LLMError(
            "anthropic",
            "Anthropic does not provide an embedding API. Use OpenAI for embeddings.",
        )

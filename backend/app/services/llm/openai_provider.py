"""OpenAI LLM provider implementation."""

import time
from typing import AsyncIterator

from openai import AsyncOpenAI

from app.core.exceptions import LLMError
from app.models.llm import LLMProvider, LLMResponse, TokenUsage
from app.services.llm.base import BaseLLMProvider


class OpenAIProvider(BaseLLMProvider):
    """OpenAI API provider."""

    provider = LLMProvider.OPENAI

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o-mini",
        embedding_model: str = "text-embedding-3-small",
    ):
        """Initialize OpenAI provider.

        Args:
            api_key: OpenAI API key
            model: Model to use for chat completions
            embedding_model: Model to use for embeddings
        """
        self.model = model
        self.embedding_model = embedding_model
        self.client = AsyncOpenAI(api_key=api_key)

    async def complete(
        self,
        prompt: str,
        system_prompt: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> LLMResponse:
        """Generate a completion using OpenAI.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature

        Returns:
            LLMResponse with generated content
        """
        messages: list[dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        start_time = time.time()

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,  # type: ignore[arg-type]
                max_tokens=max_tokens,
                temperature=temperature,
            )
        except Exception as e:
            raise LLMError("openai", str(e)) from e

        latency_ms = int((time.time() - start_time) * 1000)

        content = response.choices[0].message.content or ""
        usage = response.usage

        return LLMResponse(
            content=content,
            model=self.model,
            provider=self.provider,
            usage=TokenUsage(
                prompt_tokens=usage.prompt_tokens if usage else 0,
                completion_tokens=usage.completion_tokens if usage else 0,
                total_tokens=usage.total_tokens if usage else 0,
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
        """Stream a completion using OpenAI.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature

        Yields:
            Content chunks and final usage
        """
        messages: list[dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,  # type: ignore[arg-type]
                max_tokens=max_tokens,
                temperature=temperature,
                stream=True,
                stream_options={"include_usage": True},
            )

            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield (chunk.choices[0].delta.content, None)

                # Final chunk with usage
                if chunk.usage:
                    yield (
                        "",
                        TokenUsage(
                            prompt_tokens=chunk.usage.prompt_tokens,
                            completion_tokens=chunk.usage.completion_tokens,
                            total_tokens=chunk.usage.total_tokens,
                        ),
                    )

        except Exception as e:
            raise LLMError("openai", str(e)) from e

    async def embed(self, texts: list[str]) -> tuple[list[list[float]], int]:
        """Generate embeddings using OpenAI.

        Args:
            texts: List of texts to embed

        Returns:
            Tuple of (embeddings, total_tokens_used)
        """
        if not texts:
            return [], 0

        try:
            response = await self.client.embeddings.create(
                model=self.embedding_model,
                input=texts,
            )
        except Exception as e:
            raise LLMError("openai", str(e)) from e

        embeddings = [item.embedding for item in response.data]
        total_tokens = response.usage.total_tokens

        return embeddings, total_tokens

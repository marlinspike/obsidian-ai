"""OpenRouter LLM provider implementation."""

import time
from typing import AsyncIterator

import httpx

from app.core.exceptions import LLMError
from app.models.llm import LLMProvider, LLMResponse, TokenUsage
from app.services.llm.base import BaseLLMProvider


class OpenRouterProvider(BaseLLMProvider):
    """OpenRouter API provider for accessing multiple models."""

    provider = LLMProvider.OPENROUTER
    BASE_URL = "https://openrouter.ai/api/v1"

    def __init__(
        self,
        api_key: str,
        model: str = "openai/gpt-4o-mini",
        site_url: str | None = None,
        app_name: str = "obsidian-ai",
    ):
        """Initialize OpenRouter provider.

        Args:
            api_key: OpenRouter API key
            model: Model to use (format: provider/model)
            site_url: Your site URL (for rankings)
            app_name: Your app name
        """
        self.model = model
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": site_url or "https://github.com/obsidian-ai",
            "X-Title": app_name,
            "Content-Type": "application/json",
        }

    async def complete(
        self,
        prompt: str,
        system_prompt: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> LLMResponse:
        """Generate a completion using OpenRouter.

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

        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(
                    f"{self.BASE_URL}/chat/completions",
                    headers=self.headers,
                    json={
                        "model": self.model,
                        "messages": messages,
                        "max_tokens": max_tokens,
                        "temperature": temperature,
                    },
                )
                response.raise_for_status()
                data = response.json()
            except httpx.HTTPStatusError as e:
                raise LLMError("openrouter", f"HTTP {e.response.status_code}: {e.response.text}")
            except Exception as e:
                raise LLMError("openrouter", str(e)) from e

        latency_ms = int((time.time() - start_time) * 1000)

        content = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})

        return LLMResponse(
            content=content,
            model=self.model,
            provider=self.provider,
            usage=TokenUsage(
                prompt_tokens=usage.get("prompt_tokens", 0),
                completion_tokens=usage.get("completion_tokens", 0),
                total_tokens=usage.get("total_tokens", 0),
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
        """Stream a completion using OpenRouter.

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

        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                async with client.stream(
                    "POST",
                    f"{self.BASE_URL}/chat/completions",
                    headers=self.headers,
                    json={
                        "model": self.model,
                        "messages": messages,
                        "max_tokens": max_tokens,
                        "temperature": temperature,
                        "stream": True,
                    },
                ) as response:
                    response.raise_for_status()

                    buffer = ""
                    async for chunk in response.aiter_text():
                        buffer += chunk

                        # Process complete SSE messages
                        while "\n\n" in buffer:
                            message, buffer = buffer.split("\n\n", 1)

                            if message.startswith("data: "):
                                data_str = message[6:]
                                if data_str == "[DONE]":
                                    # Estimate usage (OpenRouter doesn't always provide final usage)
                                    yield (
                                        "",
                                        TokenUsage(
                                            prompt_tokens=0,
                                            completion_tokens=0,
                                            total_tokens=0,
                                        ),
                                    )
                                    return

                                import json

                                try:
                                    data = json.loads(data_str)
                                    if (
                                        data.get("choices")
                                        and data["choices"][0].get("delta", {}).get("content")
                                    ):
                                        yield (data["choices"][0]["delta"]["content"], None)

                                    # Check for usage in final message
                                    if data.get("usage"):
                                        yield (
                                            "",
                                            TokenUsage(
                                                prompt_tokens=data["usage"].get(
                                                    "prompt_tokens", 0
                                                ),
                                                completion_tokens=data["usage"].get(
                                                    "completion_tokens", 0
                                                ),
                                                total_tokens=data["usage"].get("total_tokens", 0),
                                            ),
                                        )
                                except json.JSONDecodeError:
                                    continue

            except httpx.HTTPStatusError as e:
                raise LLMError(
                    "openrouter", f"HTTP {e.response.status_code}: {e.response.text}"
                ) from e
            except Exception as e:
                raise LLMError("openrouter", str(e)) from e

    async def embed(self, texts: list[str]) -> tuple[list[list[float]], int]:
        """Generate embeddings using OpenRouter.

        Note: OpenRouter doesn't directly support embeddings for all models.
        This uses their embeddings endpoint if available.

        Args:
            texts: List of texts to embed

        Returns:
            Tuple of (embeddings, total_tokens_used)
        """
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(
                    f"{self.BASE_URL}/embeddings",
                    headers=self.headers,
                    json={
                        "model": "openai/text-embedding-3-small",  # Default embedding model
                        "input": texts,
                    },
                )
                response.raise_for_status()
                data = response.json()
            except httpx.HTTPStatusError as e:
                raise LLMError(
                    "openrouter", f"HTTP {e.response.status_code}: {e.response.text}"
                ) from e
            except Exception as e:
                raise LLMError("openrouter", str(e)) from e

        embeddings = [item["embedding"] for item in data["data"]]
        total_tokens = data.get("usage", {}).get("total_tokens", 0)

        return embeddings, total_tokens

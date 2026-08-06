from abc import ABC, abstractmethod

from app.core.config import settings


class LLMClient(ABC):
    @abstractmethod
    async def complete(self, system_prompt: str, user_message: str) -> str:
        raise NotImplementedError


class AnthropicLLMClient(LLMClient):
    def __init__(self, api_key: str, model: str):
        # Imported lazily so the `anthropic` package is only required when an API key is
        # actually configured — keeps local/CI runs dependency-light.
        from anthropic import AsyncAnthropic

        self._client = AsyncAnthropic(api_key=api_key)
        self._model = model

    async def complete(self, system_prompt: str, user_message: str) -> str:
        response = await self._client.messages.create(
            model=self._model,
            max_tokens=1024,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
        )
        return "".join(block.text for block in response.content if block.type == "text")


class NullLLMClient(LLMClient):
    """Used when no LLM API key is configured, so the service still starts and its
    endpoints remain testable (contract-level) without network access or secrets."""

    async def complete(self, system_prompt: str, user_message: str) -> str:
        return (
            "[AI Copilot is not configured — set ANTHROPIC_API_KEY to enable live answers.] "
            f"Received question: {user_message[:200]}"
        )


def get_llm_client() -> LLMClient:
    if settings.anthropic_api_key:
        return AnthropicLLMClient(api_key=settings.anthropic_api_key, model=settings.llm_model)
    return NullLLMClient()

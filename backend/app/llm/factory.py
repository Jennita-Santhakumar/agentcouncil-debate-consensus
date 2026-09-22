"""Single seam for LLM construction so agent code stays provider-agnostic.

LLM_PROVIDER=ollama (default) uses a local llama3.2:3b via langchain-ollama.
LLM_PROVIDER=anthropic swaps in ChatAnthropic with no other code changes required.
"""
from langchain_core.language_models.chat_models import BaseChatModel

from app.config import get_settings


def get_llm(temperature: float = 0.7) -> BaseChatModel:
    settings = get_settings()

    if settings.llm_provider == "anthropic":
        from langchain_anthropic import ChatAnthropic

        if not settings.anthropic_api_key:
            raise RuntimeError("LLM_PROVIDER=anthropic requires ANTHROPIC_API_KEY to be set")
        return ChatAnthropic(
            model=settings.anthropic_model,
            api_key=settings.anthropic_api_key,
            temperature=temperature,
        )

    from langchain_ollama import ChatOllama

    return ChatOllama(
        model=settings.ollama_model,
        base_url=settings.ollama_base_url,
        temperature=temperature,
    )

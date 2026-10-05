from app.providers.base import LLMProvider
from app.providers.mock_provider import MockProvider
from app.providers.groq_provider import GroqProvider
from app.providers.gemini_provider import GeminiProvider
from app.providers.openai_provider import OpenAIProvider
from app.providers.anthropic_provider import AnthropicProvider
from app.core.config import settings
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)

_FREE_PROVIDERS = {"mock", "groq", "gemini"}


import asyncio

class LLMService:
    def __init__(self) -> None:
        self.providers: dict[str, LLMProvider] = {
            "mock": MockProvider(),
            "groq": GroqProvider(),
            "gemini": GeminiProvider(),
            "openai": OpenAIProvider(),
            "anthropic": AnthropicProvider(),
        }

    def get_provider(self, name: str) -> LLMProvider:
        provider_name = (name or settings.DEFAULT_LLM_PROVIDER).lower().strip()
        if provider_name not in settings.ALLOWED_PROVIDERS:
            raise HTTPException(status_code=403, detail=f"Provider '{provider_name}' is not allowed.")
        if provider_name not in self.providers:
            raise HTTPException(status_code=400, detail=f"Provider '{provider_name}' is not implemented.")
        return self.providers[provider_name]

    def available_providers(self) -> list[dict]:
        key_map = {
            "groq": settings.GROQ_API_KEY,
            "gemini": settings.GEMINI_API_KEY,
            "openai": settings.OPENAI_API_KEY,
            "anthropic": settings.ANTHROPIC_API_KEY,
        }
        model_map = {
            "groq": settings.GROQ_MODEL,
            "gemini": settings.GEMINI_MODEL,
            "openai": settings.OPENAI_MODEL,
            "anthropic": settings.ANTHROPIC_MODEL,
            "mock": "mock",
        }
        result = []
        for name in settings.ALLOWED_PROVIDERS:
            result.append({
                "name": name,
                "configured": name == "mock" or bool(key_map.get(name, "")),
                "default_model": model_map.get(name, ""),
                "free": name in _FREE_PROVIDERS,
            })
        return result

    async def generate(self, provider_name: str, messages: list, model: str, temperature: float) -> str:
        provider = self.get_provider(provider_name)
        resolved_model = model or settings.DEFAULT_MODEL
        
        max_retries = 4
        delay = 2.0
        
        for attempt in range(max_retries):
            try:
                return await provider.generate(messages, resolved_model, temperature)
            except HTTPException as e:
                # Catch Rate Limits (429) or Bad Gateway / Overload (502, 503)
                if e.status_code in (429, 502, 503) and attempt < max_retries - 1:
                    logger.warning("Provider %s overloaded/rate-limited (HTTP %s). Retrying in %ss (Attempt %s/%s)", 
                                   provider_name, e.status_code, delay, attempt + 1, max_retries)
                    await asyncio.sleep(delay)
                    delay *= 2.0  # Exponential backoff
                else:
                    raise


llm_service = LLMService()

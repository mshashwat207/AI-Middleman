from app.providers.base import LLMProvider
from app.providers.mock_provider import MockProvider
from app.providers.openai_provider import OpenAIProvider
from app.core.config import settings
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        self.providers = {
            "mock": MockProvider(),
            "openai": OpenAIProvider()
            # other providers could be added here
        }

    def get_provider(self, name: str) -> LLMProvider:
        provider_name = name.lower() if name else settings.DEFAULT_LLM_PROVIDER
        
        if provider_name not in settings.ALLOWED_PROVIDERS:
            raise HTTPException(status_code=403, detail="Provider not allowed by policy.")
            
        if provider_name not in self.providers:
            raise HTTPException(status_code=400, detail=f"Provider {provider_name} not implemented.")
            
        return self.providers[provider_name]

    async def generate(self, provider_name: str, messages: list, model: str, temperature: float) -> str:
        provider = self.get_provider(provider_name)
        model = model or settings.DEFAULT_MODEL
        
        # We can implement retries/timeouts here for resilience, but the provider abstractions 
        # may also handle them. We wrap the call.
        return await provider.generate(messages, model, temperature)

llm_service = LLMService()

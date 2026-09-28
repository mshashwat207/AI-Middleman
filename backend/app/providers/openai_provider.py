from typing import List, Dict, Any
from app.providers.base import LLMProvider
from app.core.config import settings
import logging
from fastapi import HTTPException
try:
    import openai
except ImportError:
    openai = None

logger = logging.getLogger(__name__)

class OpenAIProvider(LLMProvider):
    def __init__(self):
        if not settings.OPENAI_API_KEY:
            logger.warning("OPENAI_API_KEY is not set.")
        if openai:
            self.client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        else:
            self.client = None

    async def generate(self, messages: List[Dict[str, str]], model: str, temperature: float, **kwargs) -> str:
        if not self.client:
            raise HTTPException(status_code=500, detail="OpenAI package not installed or client not initialized.")
        if not settings.OPENAI_API_KEY:
            raise HTTPException(status_code=500, detail="OPENAI_API_KEY is missing.")
            
        try:
            response = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                **kwargs
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}")
            # Do NOT leak raw prompts or PII in the error!
            raise HTTPException(status_code=502, detail="External LLM Provider Error")

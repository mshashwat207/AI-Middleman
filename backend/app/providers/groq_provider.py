from typing import List, Dict
from app.providers.base import LLMProvider
from app.core.config import settings
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)

try:
    from groq import AsyncGroq
except ImportError:
    AsyncGroq = None


class GroqProvider(LLMProvider):
    def __init__(self) -> None:
        if not settings.GROQ_API_KEY:
            logger.warning("GROQ_API_KEY is not set.")
        if AsyncGroq and settings.GROQ_API_KEY:
            self.client = AsyncGroq(api_key=settings.GROQ_API_KEY)
        else:
            self.client = None

    async def generate(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float,
        **kwargs,
    ) -> str:
        if not AsyncGroq:
            raise HTTPException(status_code=500, detail="groq package not installed.")
        if not self.client:
            raise HTTPException(status_code=500, detail="GROQ_API_KEY is not configured.")

        try:
            response = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=min(temperature, 1.0),
                max_tokens=2048,
            )
            return response.choices[0].message.content
        except Exception as exc:
            logger.error("Groq API error: %s", exc)
            raise HTTPException(status_code=502, detail="Groq provider error.")

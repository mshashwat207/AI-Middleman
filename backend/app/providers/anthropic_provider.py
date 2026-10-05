from typing import List, Dict
from app.providers.base import LLMProvider
from app.core.config import settings
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)

try:
    import anthropic as anthropic_sdk
except ImportError:
    anthropic_sdk = None


class AnthropicProvider(LLMProvider):
    def __init__(self) -> None:
        if not settings.ANTHROPIC_API_KEY:
            logger.warning("ANTHROPIC_API_KEY is not set.")
        if anthropic_sdk and settings.ANTHROPIC_API_KEY:
            self.client = anthropic_sdk.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        else:
            self.client = None

    async def generate(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float,
        **kwargs,
    ) -> str:
        if not anthropic_sdk:
            raise HTTPException(status_code=500, detail="anthropic package not installed.")
        if not self.client:
            raise HTTPException(status_code=500, detail="ANTHROPIC_API_KEY is not configured.")

        try:
            system_parts = [m["content"] for m in messages if m["role"] == "system"]
            user_messages = [
                {"role": m["role"], "content": m["content"]}
                for m in messages
                if m["role"] in ("user", "assistant")
            ]

            kwargs_call: Dict = {"model": model, "max_tokens": 4096, "temperature": temperature, "messages": user_messages}
            if system_parts:
                kwargs_call["system"] = "\n\n".join(system_parts)

            response = await self.client.messages.create(**kwargs_call)
            return response.content[0].text
        except Exception as exc:
            logger.error("Anthropic API error: %s", exc)
            raise HTTPException(status_code=502, detail="Anthropic provider error.")

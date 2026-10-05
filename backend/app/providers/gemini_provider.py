from typing import List, Dict
from app.providers.base import LLMProvider
from app.core.config import settings
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)

try:
    import google.generativeai as genai
except ImportError:
    genai = None


class GeminiProvider(LLMProvider):
    def __init__(self) -> None:
        if not settings.GEMINI_API_KEY:
            logger.warning("GEMINI_API_KEY is not set.")
        if genai and settings.GEMINI_API_KEY:
            genai.configure(api_key=settings.GEMINI_API_KEY)

    async def generate(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float,
        **kwargs,
    ) -> str:
        if not genai:
            raise HTTPException(status_code=500, detail="google-generativeai package not installed.")
        if not settings.GEMINI_API_KEY:
            raise HTTPException(status_code=500, detail="GEMINI_API_KEY is not configured.")

        try:
            import asyncio

            gemini_model = genai.GenerativeModel(model_name=model)

            history = []
            system_text = None
            for msg in messages:
                if msg["role"] == "system":
                    system_text = msg["content"]
                elif msg["role"] == "user":
                    parts = []
                    if system_text:
                        parts.append(system_text)
                        system_text = None
                    parts.append(msg["content"])
                    history.append({"role": "user", "parts": parts})
                elif msg["role"] == "assistant":
                    history.append({"role": "model", "parts": [msg["content"]]})

            last = history.pop() if history else {"role": "user", "parts": [""]}
            chat = gemini_model.start_chat(history=history)

            generation_config = genai.types.GenerationConfig(temperature=temperature)

            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: chat.send_message(
                    last["parts"],
                    generation_config=generation_config,
                ),
            )
            return response.text
        except Exception as exc:
            logger.error("Gemini API error: %s", exc)
            raise HTTPException(status_code=502, detail="Gemini provider error.")

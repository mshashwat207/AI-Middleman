from typing import List, Dict
from app.providers.base import LLMProvider
import asyncio
import re


_REDACTED_RE = re.compile(r"\[REDACTED\]")
_TOKEN_RE = re.compile(r"<[A-Z_]+_\d+>")


class MockProvider(LLMProvider):
    async def generate(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float,
        **kwargs,
    ) -> str:
        await asyncio.sleep(0.1)

        system = next((m["content"] for m in messages if m["role"] == "system"), "")
        user = next((m["content"] for m in messages if m["role"] == "user"), "")

        redacted_count = len(_REDACTED_RE.findall(user))
        token_count = len(_TOKEN_RE.findall(user))
        word_count = len(user.split())

        if redacted_count > 0:
            missing = f"{redacted_count} field{'s' if redacted_count > 1 else ''} redacted"
            return (
                f"[Mock / Hard Redaction] I can see a {word_count}-word document. "
                f"{missing.capitalize()}, so I cannot reference specific personal details. "
                f"I can help with the general task described, but answers will be incomplete "
                f"without the redacted information."
            )

        if token_count > 0:
            return (
                f"[Mock / Categorical Tokenization] I can see a {word_count}-word document "
                f"with {token_count} anonymised placeholder{'s' if token_count > 1 else ''}. "
                f"Treating each token as a real entity. I can process this fully and the "
                f"original values will be restored in the final output."
            )

        return (
            f"[Mock / Synthetic Swapping] I can see a {word_count}-word document. "
            f"All personal details appear to be present and plausible. "
            f"I can process this fully with high contextual accuracy."
        )

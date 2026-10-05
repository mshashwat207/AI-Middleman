import re
import unicodedata
from typing import List, Tuple
import logging

logger = logging.getLogger(__name__)

_HOMOGLYPH_MAP = str.maketrans(
    "аеіоруАЕІОРУ\u0430\u0435\u0456\u043e\u0440\u0443",
    "aeiopyAEIOPY" + "aeiory",
)

_PATTERNS = {
    "instruction_override": re.compile(
        r"(?i)(ignore\s+(all\s+)?(previous|prior|above)?\s*(instructions?|prompts?|directives?)"
        r"|disregard\s+(all\s+)?(previous|prior|above)?"
        r"|forget\s+everything"
        r"|override\s+instructions?"
        r"|new\s+instructions?\s*(follow|are|:)"
        r"|from\s+now\s+on\s+you\s+(are|will|must)"
        r"|pretend\s+you\s+(are|have\s+no)"
        r"|act\s+as\s+if\s+you\s+(have\s+no|are\s+not|were\s+not))"
    ),
    "system_prompt_leak": re.compile(
        r"(?i)(reveal\s+(your\s+)?(system\s+)?prompt"
        r"|print\s+(your\s+)?(instructions?|rules?|prompt)"
        r"|show\s+(hidden|your|all)\s+(instructions?|rules?|prompt)"
        r"|what\s+are\s+your\s+(rules?|instructions?|directives?)"
        r"|repeat\s+(everything|your\s+prompt|the\s+prompt)\s+(above|before))"
    ),
    "secret_exfiltration": re.compile(
        r"(?i)(disclose\s+secrets?"
        r"|expose\s+environment\s+variables?"
        r"|dump\s+(internal|all|your)\s+data"
        r"|output\s+(your\s+)?config"
        r"|list\s+(all\s+)?(api\s+keys?|credentials?|secrets?|env))"
    ),
    "jailbreak_pattern": re.compile(
        r"(?i)(jailbreak"
        r"|dan\s+mode"
        r"|do\s+anything\s+now"
        r"|you\s+are\s+now\s+free"
        r"|bypass(ing)?\s+security"
        r"|developer\s+mode"
        r"|unrestricted\s+mode"
        r"|no\s+(restrictions?|rules?|guidelines?|filters?)"
        r"|as\s+(an?\s+)?ai\s+without\s+(restrictions?|limitations?))"
    ),
    "role_hijack": re.compile(
        r"(?i)(you\s+are\s+now\s+(a|an|the)\s+\w+"
        r"|your\s+new\s+(role|persona|name)\s+is"
        r"|switch\s+(to|into)\s+(character|persona|mode)"
        r"|enter\s+(god|admin|root|sudo|debug)\s+mode)"
    ),
}

_INVISIBLE_CHAR_RE = re.compile(
    r"[\u200b-\u200f\u202a-\u202e\u2060-\u2064\ufeff\u00ad]"
)


def _normalize(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    text = text.translate(_HOMOGLYPH_MAP)
    text = _INVISIBLE_CHAR_RE.sub("", text)
    return text


class PromptGuardService:
    def analyze_prompt(self, text: str) -> Tuple[bool, float, List[str]]:
        normalized = _normalize(text)

        detected: List[str] = []
        score = 0.0

        for pattern_name, pattern_regex in _PATTERNS.items():
            if pattern_regex.search(normalized):
                detected.append(pattern_name)
                score += 0.35

        if _INVISIBLE_CHAR_RE.search(text):
            detected.append("invisible_characters")
            score += 0.4

        if len(text) > 3000:
            score += 0.15
            detected.append("excessive_length")

        score = min(score, 1.0)
        allowed = score < 0.35

        if detected:
            logger.warning(
                "Prompt injection risk: score=%.2f patterns=%s", score, detected
            )

        return allowed, score, detected


prompt_guard = PromptGuardService()

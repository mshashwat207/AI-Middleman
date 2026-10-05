import re
from dataclasses import dataclass
from typing import List
import logging

logger = logging.getLogger(__name__)

_TITLES = (
    r"ceo|cto|coo|cfo|cmo|ciso|founder|co-founder|president|vice president|vp|"
    r"chairman|chairperson|director|managing director|md|executive director|"
    r"prime minister|chief minister|minister|governor|secretary|commissioner|"
    r"judge|chief justice|justice|magistrate|collector|sp|ig|dgp|"
    r"general|colonel|major|captain|admiral|marshal|"
    r"head|chief|lead|principal|dean|provost|rector|"
    r"doctor|dr|professor|prof|inspector|superintendent|"
    r"ambassador|consul|attaché|attache|envoy|"
    r"owner|proprietor|partner|trustee"
)

_ORG_PREPS = r"of|at|for|in|from"

_ROLE_ORG_RE = re.compile(
    rf"(?i:\b(?:{_TITLES})\s+(?:{_ORG_PREPS})\s+)[A-Z][A-Za-z0-9\s&\-\.]+"
)

_SUPERLATIVE_RE = re.compile(
    r"\b(india['\u2019]?s|world['\u2019]?s|country['\u2019]?s|"
    r"the\s+(?:only|first|last|most\s+\w+|youngest|oldest|richest|poorest|"
    r"most\s+famous|most\s+senior|most\s+junior))\s+"
    r"(?:\w+\s+){0,3}\w+\b",
    re.IGNORECASE,
)

_RELATIONAL_RE = re.compile(
    r"\b(?:my|his|her|their|our)\s+"
    r"(?:husband|wife|spouse|partner|father|mother|dad|mum|mom|son|daughter|"
    r"brother|sister|uncle|aunt|grandfather|grandmother|boss|manager|"
    r"employer|employee|client|patient|lawyer|doctor|friend|colleague)\b",
    re.IGNORECASE,
)

_CASE_LOCATOR_RE = re.compile(
    r"\b(?:patient|accused|defendant|plaintiff|suspect|victim|inmate|"
    r"resident|employee|student|candidate)\s+"
    r"(?:in|at|of|from|admitted\s+to|registered\s+at|enrolled\s+at)\s+"
    r"[A-Z][A-Za-z0-9\s\-\.]+",
    re.IGNORECASE,
)

_QUASI_IDENTIFIERS = [
    re.compile(r"\b\d{1,3}\s*(?:years?\s*old|yr\s*old|y\.?o\.?)\b", re.IGNORECASE),
    re.compile(r"\b(?:male|female|man|woman|boy|girl|transgender|non-binary)\b", re.IGNORECASE),
    re.compile(
        r"\b(?:doctor|engineer|lawyer|teacher|nurse|architect|chartered accountant|"
        r"ca|cs|pilot|police|soldier|journalist|professor|scientist|researcher)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:january|february|march|april|may|june|july|august|september|"
        r"october|november|december)\s+\d{4}\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:mumbai|delhi|bangalore|bengaluru|chennai|hyderabad|kolkata|pune|"
        r"ahmedabad|surat|jaipur|lucknow|kanpur|nagpur|indore|bhopal|"
        r"new delhi|new york|london|dubai|singapore)\b",
        re.IGNORECASE,
    ),
]

_QUASI_THRESHOLD = 3


@dataclass
class IndirectPIIWarning:
    category: str
    snippet: str
    reason: str


class IndirectPIIDetector:
    def scan(self, text: str, threshold: int = 3) -> List[IndirectPIIWarning]:
        warnings: List[IndirectPIIWarning] = []

        for match in _ROLE_ORG_RE.finditer(text):
            snippet = match.group(0).strip()
            if len(snippet) > 6:
                warnings.append(IndirectPIIWarning(
                    category="ROLE_IDENTITY",
                    snippet=snippet[:120],
                    reason=(
                        "A role combined with a named organisation can identify a specific individual "
                        "even without a name. Example: 'CEO of Twitter' resolves to a known person."
                    ),
                ))

        for match in _SUPERLATIVE_RE.finditer(text):
            snippet = match.group(0).strip()
            if len(snippet) > 6:
                warnings.append(IndirectPIIWarning(
                    category="SUPERLATIVE_IDENTITY",
                    snippet=snippet[:120],
                    reason=(
                        "A superlative description combined with a role uniquely identifies an individual. "
                        "Example: 'India's first female Supreme Court judge'."
                    ),
                ))

        for match in _RELATIONAL_RE.finditer(text):
            warnings.append(IndirectPIIWarning(
                category="RELATIONAL_REFERENCE",
                snippet=match.group(0).strip(),
                reason=(
                    "A relational reference such as 'my husband' or 'her doctor' can identify "
                    "a person when combined with other context in the same document."
                ),
            ))

        for match in _CASE_LOCATOR_RE.finditer(text):
            snippet = match.group(0).strip()
            if len(snippet) > 10:
                warnings.append(IndirectPIIWarning(
                    category="LOCATOR_REFERENCE",
                    snippet=snippet[:120],
                    reason=(
                        "A role combined with a specific institution or case number can identify "
                        "an individual. Example: 'the patient at AIIMS Delhi admitted on Tuesday'."
                    ),
                ))

        matched_quasi = [p for p in _QUASI_IDENTIFIERS if p.search(text)]
        if len(matched_quasi) >= threshold:
            warnings.append(IndirectPIIWarning(
                category="QUASI_IDENTIFIER_CLUSTER",
                snippet=f"{len(matched_quasi)} identifying attributes detected",
                reason=(
                    f"The text contains {len(matched_quasi)} individually non-PII attributes "
                    "(age, gender, profession, location, date) that together may uniquely "
                    "identify a person even without a name. This is a k-anonymity risk."
                ),
            ))

        seen: set[str] = set()
        deduped: List[IndirectPIIWarning] = []
        for w in warnings:
            key = (w.category, w.snippet[:40])
            if key not in seen:
                seen.add(key)
                deduped.append(w)

        if deduped:
            logger.warning(
                "IndirectPII: %d warnings (%s)",
                len(deduped),
                [w.category for w in deduped],
            )

        return deduped


indirect_pii_detector = IndirectPIIDetector()

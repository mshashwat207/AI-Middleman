from typing import List, Dict, Tuple
from app.schemas.masking import DetectedEntity
from app.schemas.benchmark import EntityDetail
from faker import Faker
import re
import logging

logger = logging.getLogger(__name__)

from langdetect import detect

_FAKER_CACHE = {}

def _get_faker(text: str) -> Faker:
    try:
        lang = detect(text)
    except Exception:
        lang = "en"
    
    locale_map = {
        "hi": "hi_IN",
        "es": "es_ES",
        "fr": "fr_FR",
        "de": "de_DE",
        "it": "it_IT",
        "ja": "ja_JP",
        "en": "en_US",
    }
    locale = locale_map.get(lang, "en_US")
    
    if locale not in _FAKER_CACHE:
        _FAKER_CACHE[locale] = Faker(locale)
    return _FAKER_CACHE[locale]

def _get_synthetic(entity_type: str, fake: Faker) -> str:
    if entity_type == "PERSON": return fake.name()
    elif entity_type == "EMAIL": return fake.email()
    elif entity_type == "PHONE": return fake.phone_number()
    elif entity_type == "LOCATION": return fake.city()
    elif entity_type == "ORGANIZATION": return fake.company()
    elif entity_type == "DATE": return fake.date()
    elif entity_type == "CREDIT_CARD": return fake.credit_card_number(card_type=None)
    elif entity_type == "ACCOUNT": return str(fake.random_number(digits=10, fix_len=True))
    elif entity_type == "IP_ADDRESS": return fake.ipv4()
    elif entity_type == "URL": return fake.url()
    elif entity_type == "ROLE": return fake.job()
    elif entity_type == "MONEY": return f"${fake.random_number(digits=3, fix_len=False)},000"
    elif entity_type == "AADHAAR": 
        return f"{fake.random_number(digits=4, fix_len=True)} {fake.random_number(digits=4, fix_len=True)} {fake.random_number(digits=4, fix_len=True)}"
    elif entity_type == "PAN":
        return "".join(fake.random_letters(length=5)).upper() + str(fake.random_number(digits=4, fix_len=True)) + fake.random_letter().upper()
    else:
        return fake.lexify("????????")


def _sorted_desc(entities: List[DetectedEntity]) -> List[DetectedEntity]:
    return sorted(entities, key=lambda e: e.start, reverse=True)


def _expand_name_parts(value: str, synthetic: str, mapping: Dict[str, str], value_to_fake: Dict[str, str]) -> None:
    real_parts = [p for p in value.split() if len(p) > 1]
    # Remove common Faker prefixes to align first names correctly
    fake_parts = [p for p in synthetic.split() if p not in ["Mr.", "Mrs.", "Ms.", "Miss", "Dr.", "Prof."]]
    
    if len(real_parts) >= 1 and len(fake_parts) >= 1:
        mapping[fake_parts[0]] = real_parts[0]
        value_to_fake[real_parts[0]] = fake_parts[0]
        if len(fake_parts) > 1 and len(real_parts) > 1:
            mapping[fake_parts[-1]] = real_parts[-1]
            value_to_fake[real_parts[-1]] = fake_parts[-1]


class ComparativePrivacyEngine:

    def hard_redact(
        self, text: str, entities: List[DetectedEntity]
    ) -> Tuple[str, Dict[str, str], List[EntityDetail]]:
        result = text
        table: List[EntityDetail] = []
        for entity in _sorted_desc(entities):
            result = result[: entity.start] + "[REDACTED]" + result[entity.end:]
            table.append(EntityDetail(
                entity_type=entity.entity_type,
                real_value=entity.value,
                fake_value="[REDACTED]",
                confidence=entity.confidence,
            ))
        table.reverse()
        return result, {}, table

    def categorical_tokenize(
        self, text: str, entities: List[DetectedEntity]
    ) -> Tuple[str, Dict[str, str], List[EntityDetail]]:
        result = text
        mapping: Dict[str, str] = {}
        value_to_token: Dict[str, str] = {}
        type_counters: Dict[str, int] = {}
        table: List[EntityDetail] = []

        for entity in _sorted_desc(entities):
            if entity.value in value_to_token:
                token = value_to_token[entity.value]
            else:
                count = type_counters.get(entity.entity_type, 0) + 1
                type_counters[entity.entity_type] = count
                token = f"<{entity.entity_type}_{count}>"
                value_to_token[entity.value] = token
                mapping[token] = entity.value
                table.append(EntityDetail(
                    entity_type=entity.entity_type,
                    real_value=entity.value,
                    fake_value=token,
                    confidence=entity.confidence,
                ))
            result = result[: entity.start] + token + result[entity.end:]

        table.reverse()
        return result, mapping, table

    def synthetic_swap(
        self, text: str, entities: List[DetectedEntity]
    ) -> Tuple[str, Dict[str, str], List[EntityDetail]]:
        result = text
        mapping: Dict[str, str] = {}
        value_to_fake: Dict[str, str] = {}
        table: List[EntityDetail] = []
        
        fake = _get_faker(text)
        
        # Pre-compute fake names sorting by length descending to preserve co-reference
        # so that "Rishi Goyal" sets the fake name for "Rishi" before "Rishi" is evaluated.
        for entity in sorted(entities, key=lambda e: len(e.value), reverse=True):
            if entity.value not in value_to_fake:
                synthetic = _get_synthetic(entity.entity_type, fake)
                value_to_fake[entity.value] = synthetic
                mapping[synthetic] = entity.value
                if entity.entity_type == "PERSON":
                    _expand_name_parts(entity.value, synthetic, mapping, value_to_fake)

        for entity in _sorted_desc(entities):
            synthetic = value_to_fake[entity.value]
            table.append(EntityDetail(
                entity_type=entity.entity_type,
                real_value=entity.value,
                fake_value=synthetic,
                confidence=entity.confidence,
            ))
            result = result[: entity.start] + synthetic + result[entity.end:]

        table.reverse()
        return result, mapping, table

    def detokenize(self, text: str, mapping: Dict[str, str]) -> str:
        if not mapping:
            return text
        pattern = re.compile(
            "|".join(re.escape(k) for k in sorted(mapping.keys(), key=len, reverse=True))
        )
        return pattern.sub(lambda m: mapping[m.group(0)], text)


comparative_engine = ComparativePrivacyEngine()

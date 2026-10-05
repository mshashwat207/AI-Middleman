from typing import List
from presidio_analyzer import AnalyzerEngine, PatternRecognizer, Pattern
from app.schemas.masking import DetectedEntity
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class PIIDetectorService:
    def __init__(self):
        try:
            self.analyzer = AnalyzerEngine()
        except OSError as exc:
            logger.error("spaCy model missing. Run: python -m spacy download en_core_web_lg")
            raise exc
        self._add_custom_recognizers()

    def _add_custom_recognizers(self):
        self.analyzer.registry.add_recognizer(PatternRecognizer(
            supported_entity="ACCOUNT",
            patterns=[Pattern("account_number", r"\b[0-9]{9,18}\b", 1.0)],
        ))

        self.analyzer.registry.add_recognizer(PatternRecognizer(
            supported_entity="IN_PHONE",
            patterns=[
                Pattern("in_phone_intl", r"\+91[\s\-]?[6-9]\d{9}\b", 1.0),
                Pattern("in_phone_local", r"\b[6-9]\d{9}\b", 1.0),
                Pattern("in_phone_std", r"\b0[1-9]\d{1,2}[\s\-]\d{6,8}\b", 1.0),
            ],
        ))

        self.analyzer.registry.add_recognizer(PatternRecognizer(
            supported_entity="AADHAAR",
            patterns=[
                Pattern("aadhaar_spaced", r"\b[2-9]\d{3}\s\d{4}\s\d{4}\b", 1.0),
                Pattern("aadhaar_plain", r"\b[2-9]\d{11}\b", 1.0),
            ],
        ))

        self.analyzer.registry.add_recognizer(PatternRecognizer(
            supported_entity="PAN",
            patterns=[Pattern("pan_card", r"\b[A-Z]{5}[0-9]{4}[A-Z]\b", 1.0)],
        ))

        self.analyzer.registry.add_recognizer(PatternRecognizer(
            supported_entity="DATE_TIME",
            patterns=[Pattern("date_slash", r"\b\d{1,2}/\d{1,2}/\d{2,4}\b", 1.0)],
        ))

        _TITLES = (
            r"\b(ceo|cto|coo|cfo|cmo|ciso|founder|co-founder|president|vice president|vp|"
            r"chairman|chairperson|director|managing director|md|executive director|"
            r"prime minister|chief minister|minister|governor|secretary|commissioner|"
            r"judge|chief justice|justice|magistrate|collector|sp|ig|dgp|"
            r"general|colonel|major|captain|admiral|marshal|"
            r"head|chief|lead|principal|dean|provost|rector|"
            r"doctor|dr|professor|prof|inspector|superintendent|"
            r"ambassador|consul|attaché|attache|envoy|"
            r"owner|proprietor|partner|trustee)\b"
        )
        self.analyzer.registry.add_recognizer(PatternRecognizer(
            supported_entity="ROLE",
            patterns=[Pattern("job_role", _TITLES, 0.75)],
        ))

        self.analyzer.registry.add_recognizer(PatternRecognizer(
            supported_entity="LOCATION",
            patterns=[Pattern("indian_address", r"\b\d+\s[A-Za-z\s]+(?:Road|St|Street|Ave|Marg|Lane|Blvd|Layout|Nagar)(?:,\s[A-Za-z\s]+)?(?:\s\d{6})?\b", 1.0)],
        ))

        self.analyzer.registry.add_recognizer(PatternRecognizer(
            supported_entity="ORGANIZATION",
            patterns=[Pattern("org_suffix", r"\b[A-Z][A-Za-z]+\s(?:Innovations|Corp|Inc|LLC|Ltd|Private Limited|Hospital|Institute)\b", 1.0)],
        ))

        self.analyzer.registry.add_recognizer(PatternRecognizer(
            supported_entity="MONEY",
            patterns=[Pattern("currency_amount", r"(?:\$|€|£|₹|Rs\.?)\s?\d+(?:,\d{3})*(?:\.\d{2})?\b", 1.0)],
        ))

    def detect_entities(self, text: str, language: str = "en") -> List[DetectedEntity]:
        results = self.analyzer.analyze(
            text=text,
            language=language,
            entities=[
                "PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER", "LOCATION",
                "ORGANIZATION", "DATE_TIME", "ACCOUNT", "CREDIT_CARD",
                "IP_ADDRESS", "URL", "IN_PHONE", "AADHAAR", "PAN", "ROLE",
                "MONEY"
            ],
            score_threshold=settings.PII_CONFIDENCE_THRESHOLD,
        )

        entity_map = {
            "EMAIL_ADDRESS": "EMAIL",
            "PHONE_NUMBER": "PHONE",
            "DATE_TIME": "DATE",
            "IN_PHONE": "PHONE",
        }

        detected = []
        for res in results:
            mapped = entity_map.get(res.entity_type, res.entity_type)
            detected.append(DetectedEntity(
                entity_type=mapped,
                start=res.start,
                end=res.end,
                value=text[res.start:res.end],
                confidence=res.score,
            ))

        import re
        person_names = [e.value for e in detected if e.entity_type == "PERSON"]
        for full_name in person_names:
            parts = [p for p in full_name.split() if len(p) > 2]
            for part in parts:
                for match in re.finditer(r"\b" + re.escape(part) + r"\b", text):
                    detected.append(DetectedEntity(
                        entity_type="PERSON",
                        start=match.start(),
                        end=match.end(),
                        value=match.group(),
                        confidence=1.0
                    ))

        detected.sort(key=lambda x: (-x.confidence, -(x.end - x.start)))

        filtered: List[DetectedEntity] = []
        for entity in detected:
            is_overlapping = False
            for accepted in filtered:
                if max(entity.start, accepted.start) < min(entity.end, accepted.end):
                    is_overlapping = True
                    break
            
            if not is_overlapping:
                filtered.append(entity)
                
        filtered.sort(key=lambda x: x.start)

        import logging
        logger = logging.getLogger(__name__)
        logger.info("Detected %d entities. Types: %s", len(filtered), [e.entity_type for e in filtered])
        return filtered


_instance = None


def get_pii_detector() -> PIIDetectorService:
    global _instance
    if _instance is None:
        _instance = PIIDetectorService()
    return _instance

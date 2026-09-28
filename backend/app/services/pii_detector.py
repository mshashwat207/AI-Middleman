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
        except OSError as e:
            logger.error("Could not load spaCy model. Run: python -m spacy download en_core_web_lg")
            raise e
        
        self._add_custom_recognizers()

    def _add_custom_recognizers(self):
        # Account Number Recognizer
        account_pattern = Pattern(
            name="account_number_pattern",
            regex=r"\b[0-9]{8,12}\b",
            score=0.7
        )
        account_recognizer = PatternRecognizer(
            supported_entity="ACCOUNT",
            patterns=[account_pattern]
        )
        self.analyzer.registry.add_recognizer(account_recognizer)

    def detect_entities(self, text: str, language: str = "en") -> List[DetectedEntity]:
        # Perform detection
        analyzer_results = self.analyzer.analyze(
            text=text,
            language=language,
            entities=["PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER", "LOCATION", 
                      "ORGANIZATION", "DATE_TIME", "ACCOUNT", "CREDIT_CARD", 
                      "IP_ADDRESS", "URL", "US_SSN"],
            score_threshold=settings.PII_CONFIDENCE_THRESHOLD
        )
        
        # We need to map PRESIDIO entities to our standardized ones if needed
        # e.g., EMAIL_ADDRESS -> EMAIL
        entity_map = {
            "EMAIL_ADDRESS": "EMAIL",
            "PHONE_NUMBER": "PHONE",
            "DATE_TIME": "DATE",
            "US_SSN": "SSN"
        }
        
        detected_entities = []
        for res in analyzer_results:
            mapped_type = entity_map.get(res.entity_type, res.entity_type)
            detected_entities.append(
                DetectedEntity(
                    entity_type=mapped_type,
                    start=res.start,
                    end=res.end,
                    value=text[res.start:res.end],
                    confidence=res.score
                )
            )
            
        # Handle overlaps (Presidio generally handles some, but we can do a simple filter to prefer higher confidence/longer)
        # Sort by start, then by length descending
        detected_entities.sort(key=lambda x: (x.start, -(x.end - x.start)))
        
        filtered = []
        last_end = 0
        for entity in detected_entities:
            if entity.start >= last_end:
                filtered.append(entity)
                last_end = entity.end
                
        # IMPORTANT: Do not log the actual value
        logger.info(f"Detected {len(filtered)} entities in request. Types: {[e.entity_type for e in filtered]}")
        
        return filtered

# Singleton instance
pii_detector = None
def get_pii_detector() -> PIIDetectorService:
    global pii_detector
    if pii_detector is None:
        pii_detector = PIIDetectorService()
    return pii_detector

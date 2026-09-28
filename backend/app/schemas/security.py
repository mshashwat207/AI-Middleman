from pydantic import BaseModel
from typing import List

class MaskingRequest(BaseModel):
    text: str

class SecurityAnalysisResponse(BaseModel):
    pii_detected: bool
    entity_count: int
    entity_types: List[str]
    prompt_injection_detected: bool
    risk_score: float

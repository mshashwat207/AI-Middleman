from pydantic import BaseModel, Field
from typing import List, Optional

class DetectedEntity(BaseModel):
    entity_type: str = Field(..., description="Type of the detected entity, e.g., PERSON, EMAIL")
    start: int = Field(..., description="Start position in the string")
    end: int = Field(..., description="End position in the string")
    value: str = Field(..., description="The actual detected value")
    confidence: float = Field(..., description="Confidence score of the detection")

class MaskedEntityPreview(BaseModel):
    type: str
    token: str
    confidence: float

class MaskingPreviewResponse(BaseModel):
    masked_text: str
    entities: List[MaskedEntityPreview]

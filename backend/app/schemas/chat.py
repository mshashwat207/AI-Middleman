from pydantic import BaseModel, Field
from typing import Optional

class ChatRequest(BaseModel):
    message: str = Field(..., max_length=10000)
    session_id: Optional[str] = None
    provider: str = "mock"
    model_name: Optional[str] = None
    temperature: float = Field(0.7, ge=0.0, le=2.0)

class ChatSecurityMetadata(BaseModel):
    pii_detected: bool
    entities_masked: int
    prompt_risk_score: float

class ChatResponse(BaseModel):
    response: str
    security: ChatSecurityMetadata
    request_id: str

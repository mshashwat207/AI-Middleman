from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.models.database import get_db
from app.schemas.security import MaskingRequest, SecurityAnalysisResponse
from app.schemas.masking import MaskingPreviewResponse
from app.services.pii_detector import get_pii_detector
from app.services.tokenizer import tokenizer_service
from app.services.prompt_guard import prompt_guard
import uuid

router = APIRouter()

@router.post("/mask", response_model=MaskingPreviewResponse)
def mask_preview(request: MaskingRequest, db: Session = Depends(get_db)):
    """
    Demonstration endpoint to show how masking works.
    Creates a temporary session to hold the mapping.
    """
    pii_detector = get_pii_detector()
    entities = pii_detector.detect_entities(request.text)
    
    # Use a dummy session for the preview
    session_id = str(uuid.uuid4())
    
    masked_text, token_previews = tokenizer_service.tokenize(
        db=db,
        text=request.text,
        entities=entities,
        session_id=session_id
    )
    
    # Notice we DO NOT return the original value in the response
    return MaskingPreviewResponse(
        masked_text=masked_text,
        entities=token_previews
    )

@router.post("/analyze", response_model=SecurityAnalysisResponse)
def analyze_security(request: MaskingRequest):
    """
    Analyzes text for PII and prompt injection risk without storing anything.
    """
    # 1. PII
    pii_detector = get_pii_detector()
    entities = pii_detector.detect_entities(request.text)
    
    # 2. Prompt Injection
    allowed, risk_score, detected_patterns = prompt_guard.analyze_prompt(request.text)
    
    entity_types = list(set([e.entity_type for e in entities]))
    
    return SecurityAnalysisResponse(
        pii_detected=len(entities) > 0,
        entity_count=len(entities),
        entity_types=entity_types,
        prompt_injection_detected=not allowed or len(detected_patterns) > 0,
        risk_score=risk_score
    )

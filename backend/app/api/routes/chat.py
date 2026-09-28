from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.models.database import get_db
from app.schemas.chat import ChatRequest, ChatResponse, ChatSecurityMetadata
from app.services.pii_detector import get_pii_detector
from app.services.prompt_guard import prompt_guard
from app.services.tokenizer import tokenizer_service
from app.services.token_store import token_store
from app.services.llm_service import llm_service
from app.services.rehydrator import rehydrator_service
from app.services.policy_engine import policy_engine
import uuid
import time
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest, db: Session = Depends(get_db)):
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    # 1. Prompt Injection Screening
    allowed, risk_score, detected_patterns = prompt_guard.analyze_prompt(request.message)
    if not allowed and policy_engine.should_block_risk(risk_score):
        logger.warning(f"Blocked request {request_id} due to prompt injection.")
        raise HTTPException(status_code=403, detail="Security policy violation: High risk prompt detected.")

    # 2. Setup Session
    db_session = token_store.get_or_create_session(db, request.session_id)
    session_id = db_session.id
    
    # 3. PII Detection
    pii_detector = get_pii_detector()
    entities = pii_detector.detect_entities(request.message)
    
    # 4. Tokenization
    masked_text, token_previews = tokenizer_service.tokenize(
        db=db, 
        text=request.message, 
        entities=entities, 
        session_id=session_id
    )
    
    # 5. Masked LLM Request
    messages = [{"role": "user", "content": masked_text}]
    
    try:
        llm_response_text = await llm_service.generate(
            provider_name=request.provider,
            messages=messages,
            model=request.model_name,
            temperature=request.temperature
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error calling LLM: {str(e)}")
        raise HTTPException(status_code=502, detail="External LLM Provider Error")
        
    # 6. Response Security Check (e.g. prompt injection leaking through)
    resp_allowed, resp_risk_score, resp_patterns = prompt_guard.analyze_prompt(llm_response_text)
    # We might not strictly block if the LLM talks about secret patterns, but if it's very high risk...
    if not resp_allowed and policy_engine.should_block_risk(resp_risk_score):
        logger.warning(f"Blocked response {request_id} due to unsafe output.")
        raise HTTPException(status_code=403, detail="Security policy violation: Unsafe LLM response.")

    # 7. Controlled Re-Hydration
    if policy_engine.rehydration_enabled:
        final_response = rehydrator_service.rehydrate(db, llm_response_text, session_id)
    else:
        final_response = llm_response_text

    # 8. Record Audit Log
    latency_ms = (time.time() - start_time) * 1000
    from app.services.audit_service import audit_service
    audit_service.log_request(
        db=db,
        request_id=request_id,
        session_id=session_id,
        provider=request.provider,
        model=request.model_name,
        pii_entity_count=len(entities),
        entity_types=[e.entity_type for e in entities],
        prompt_risk_score=risk_score,
        blocked=False,
        latency_ms=latency_ms
    )
    
    return ChatResponse(
        response=final_response,
        security=ChatSecurityMetadata(
            pii_detected=len(entities) > 0,
            entities_masked=len(entities),
            prompt_risk_score=risk_score
        ),
        request_id=request_id
    )

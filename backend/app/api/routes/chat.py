from fastapi import APIRouter, Depends, HTTPException
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
from app.services.audit_service import audit_service
import uuid
import time
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest, db: Session = Depends(get_db)):
    request_id = str(uuid.uuid4())
    start_time = time.time()

    allowed, risk_score, detected_patterns = prompt_guard.analyze_prompt(request.message)
    if not allowed and policy_engine.should_block_risk(risk_score):
        latency_ms = (time.time() - start_time) * 1000
        audit_service.log_request(
            db=db,
            request_id=request_id,
            session_id=request.session_id,
            provider=request.provider,
            model=request.model_name,
            pii_entity_count=0,
            entity_types=[],
            prompt_risk_score=risk_score,
            blocked=True,
            latency_ms=latency_ms,
            error_category="prompt_injection",
        )
        logger.warning("Blocked request %s — prompt injection risk %.2f.", request_id, risk_score)
        raise HTTPException(
            status_code=403,
            detail="Security policy violation: high-risk prompt detected.",
        )

    db_session = token_store.get_or_create_session(db, request.session_id)
    session_id = db_session.id

    pii_detector = get_pii_detector()
    entities = pii_detector.detect_entities(request.message)

    masked_text, token_previews = tokenizer_service.tokenize(
        db=db,
        text=request.message,
        entities=entities,
        session_id=session_id,
    )

    messages = [{"role": "user", "content": masked_text}]

    try:
        llm_response_text = await llm_service.generate(
            provider_name=request.provider,
            messages=messages,
            model=request.model_name,
            temperature=request.temperature,
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("LLM call failed: %s", exc)
        raise HTTPException(status_code=502, detail="External LLM provider error.")

    resp_allowed, resp_risk_score, _ = prompt_guard.analyze_prompt(llm_response_text)
    if not resp_allowed and policy_engine.should_block_risk(resp_risk_score):
        latency_ms = (time.time() - start_time) * 1000
        audit_service.log_request(
            db=db,
            request_id=request_id,
            session_id=session_id,
            provider=request.provider,
            model=request.model_name,
            pii_entity_count=len(entities),
            entity_types=[e.entity_type for e in entities],
            prompt_risk_score=risk_score,
            blocked=True,
            latency_ms=latency_ms,
            error_category="unsafe_llm_response",
        )
        logger.warning("Blocked response %s — unsafe LLM output.", request_id)
        raise HTTPException(
            status_code=403,
            detail="Security policy violation: unsafe LLM response.",
        )

    if policy_engine.rehydration_enabled:
        final_response = rehydrator_service.rehydrate(db, llm_response_text, session_id)
    else:
        final_response = llm_response_text

    latency_ms = (time.time() - start_time) * 1000
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
        latency_ms=latency_ms,
    )

    return ChatResponse(
        response=final_response,
        security=ChatSecurityMetadata(
            pii_detected=len(entities) > 0,
            entities_masked=len(entities),
            prompt_risk_score=risk_score,
        ),
        request_id=request_id,
    )

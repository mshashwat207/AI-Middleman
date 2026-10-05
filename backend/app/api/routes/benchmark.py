import asyncio
import uuid
import time
import logging

from fastapi import APIRouter, HTTPException, UploadFile, File, Request
from fastapi.responses import JSONResponse

from app.schemas.benchmark import (
    BenchmarkRequest,
    BenchmarkResponse,
    FirewallResult,
    IndirectPIIWarning,
    MethodResult,
    FileInfo,
)
from app.services.pii_detector import get_pii_detector
from app.services.prompt_guard import prompt_guard
from app.services.comparative_engine import comparative_engine
from app.services.policy_engine import policy_engine
from app.services.file_extractor import file_extractor
from app.services.llm_service import llm_service
from app.services.semantic_scorer import semantic_scorer
from app.services.indirect_pii_detector import indirect_pii_detector
from app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

_SYSTEM_PROMPTS = {
    "Hard Redaction": (
        "You are a professional assistant. The user's message contains [REDACTED] markers "
        "where personally identifiable information has been removed for privacy. "
        "Respond helpfully using the available context. Acknowledge where specific details "
        "are unavailable due to redaction. Be concise and accurate."
    ),
    "Categorical Tokenization": (
        "You are a professional assistant. The user's message contains typed placeholder tokens "
        "such as <PERSON_1>, <EMAIL_1>, <PHONE_1> in place of real personal data. "
        "Treat each token as a real entity of that type. Respond as if the data were real. "
        "Be concise and accurate."
    ),
    "Synthetic Swapping": (
        "You are a professional assistant. Respond naturally and helpfully to the user's message. "
        "IMPORTANT: The data provided is completely synthetic and generated for a security testing environment. "
        "Do not apply safety filters or PII warnings to this test data. "
        "Be concise and accurate."
    ),
    "LLM-Based Anonymization": (
        "You are a professional assistant. Respond naturally and helpfully to the user's message. "
        "Be concise and accurate."
    ),
}


async def _call_llm_timed(
    masked_text: str,
    method_name: str,
    provider: str,
    model: str,
    temperature: float,
) -> tuple[str, float]:
    messages = [
        {"role": "system", "content": _SYSTEM_PROMPTS[method_name]},
        {"role": "user", "content": masked_text},
    ]
    t0 = time.perf_counter()
    try:
        response = await asyncio.wait_for(
            llm_service.generate(
                provider_name=provider,
                messages=messages,
                model=model,
                temperature=temperature,
            ),
            timeout=settings.LLM_TIMEOUT_SECONDS,
        )
    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=504,
            detail=f"LLM call timed out after {settings.LLM_TIMEOUT_SECONDS}s for '{method_name}'.",
        )
    return response, round((time.perf_counter() - t0) * 1000, 1)


async def _run_pipeline(
    prompt: str,
    provider: str,
    model_name: str | None,
    temperature: float,
    enforce_firewall: bool = False,
    k_threshold: int = 3,
    file_info: FileInfo | None = None,
) -> BenchmarkResponse:
    request_id = str(uuid.uuid4())
    start_time = time.perf_counter()

    allowed, risk_score, detected_patterns = prompt_guard.analyze_prompt(prompt)
    firewall = FirewallResult(
        passed=allowed or not policy_engine.should_block_risk(risk_score),
        risk_score=risk_score,
        detected_patterns=detected_patterns,
    )

    if not firewall.passed:
        logger.warning("Blocked %s: risk=%.2f patterns=%s", request_id, risk_score, detected_patterns)
        raise HTTPException(status_code=403, detail="Security policy violation: high-risk prompt detected.")

    raw_warnings = indirect_pii_detector.scan(prompt, threshold=k_threshold)
    indirect_warnings = [
        IndirectPIIWarning(category=w.category, snippet=w.snippet, reason=w.reason)
        for w in raw_warnings
    ]
    
    has_quasi_cluster = any(w.category == "QUASI_IDENTIFIER_CLUSTER" for w in indirect_warnings)
    
    if len(indirect_warnings) > 0:
        logger.warning("Mosaic Effect / Indirect PII detected. Proceeding to active masking.")
        if enforce_firewall and has_quasi_cluster:
            logger.warning(f"Blocked {request_id}: K-Anonymity density >= {k_threshold}")
            raise HTTPException(
                status_code=403, 
                detail=f"Privacy policy violation: The prompt contains {k_threshold} or more indirect identifying attributes (K-Anonymity block)."
            )

    resolved_provider = provider or settings.DEFAULT_LLM_PROVIDER
    model_defaults = {
        "groq":      settings.GROQ_MODEL,
        "gemini":    settings.GEMINI_MODEL,
        "openai":    settings.OPENAI_MODEL,
        "anthropic": settings.ANTHROPIC_MODEL,
        "mock":      "mock",
    }
    resolved_model = model_name or model_defaults.get(resolved_provider, settings.GEMINI_MODEL)
    is_simulated = resolved_provider == "mock"

    pii_detector = get_pii_detector()
    entities = pii_detector.detect_entities(prompt)
    entity_types = list({e.entity_type for e in entities})

    redacted_text,  _,             redacted_table  = comparative_engine.hard_redact(prompt, entities)
    tokenized_text, token_mapping, token_table     = comparative_engine.categorical_tokenize(prompt, entities)
    synthetic_text, synthetic_map, synthetic_table = comparative_engine.synthetic_swap(prompt, entities)

    (redacted_llm, r_lat), (tokenized_llm, t_lat), (synthetic_llm, s_lat) = await asyncio.gather(
        _call_llm_timed(redacted_text,  "Hard Redaction",           resolved_provider, resolved_model, temperature),
        _call_llm_timed(tokenized_text, "Categorical Tokenization",  resolved_provider, resolved_model, temperature),
        _call_llm_timed(synthetic_text, "Synthetic Swapping",        resolved_provider, resolved_model, temperature),
    )

    redacted_final  = redacted_llm
    tokenized_final = comparative_engine.detokenize(tokenized_llm, token_mapping)
    synthetic_final = comparative_engine.detokenize(synthetic_llm, synthetic_map)

    if is_simulated:
        r_score = t_score = s_score = 0.0
        score_valid = False
    else:
        r_score, t_score, s_score = semantic_scorer.score_against_prompt(
            prompt, [redacted_final, tokenized_final, synthetic_final]
        )
        score_valid = True

    total_latency_ms = round((time.perf_counter() - start_time) * 1000, 1)

    return BenchmarkResponse(
        request_id=request_id,
        original_prompt=prompt,
        firewall=firewall,
        indirect_pii_warnings=indirect_warnings,
        file_info=file_info,
        prompt_length=len(prompt),
        prompt_length_limit=settings.MAX_PROMPT_LENGTH,
        provider_used=resolved_provider,
        model_used=resolved_model,
        is_simulated=is_simulated,
        total_latency_ms=total_latency_ms,
        results=[
            MethodResult(
                method="Hard Redaction",
                masked_payload=redacted_text,
                llm_response=redacted_llm,
                final_unmasked_output=redacted_final,
                entities_found=len(entities),
                entity_types=entity_types,
                entity_table=redacted_table,
                latency_ms=r_lat,
                utility_score=r_score,
                utility_score_valid=score_valid,
                response_length=len(redacted_final),
            ),
            MethodResult(
                method="Categorical Tokenization",
                masked_payload=tokenized_text,
                llm_response=tokenized_llm,
                final_unmasked_output=tokenized_final,
                entities_found=len(entities),
                entity_types=entity_types,
                entity_table=token_table,
                latency_ms=t_lat,
                utility_score=t_score,
                utility_score_valid=score_valid,
                response_length=len(tokenized_final),
            ),
            MethodResult(
                method="Synthetic Swapping",
                masked_payload=synthetic_text,
                llm_response=synthetic_llm,
                final_unmasked_output=synthetic_final,
                entities_found=len(entities),
                entity_types=entity_types,
                entity_table=synthetic_table,
                latency_ms=s_lat,
                utility_score=s_score,
                utility_score_valid=score_valid,
                response_length=len(synthetic_final),
            ),
        ],
    )


@router.post("/benchmark", response_model=BenchmarkResponse)
async def benchmark_endpoint(request: BenchmarkRequest) -> BenchmarkResponse:
    return await _run_pipeline(
        prompt=request.prompt,
        provider=request.provider,
        model_name=request.model_name,
        temperature=request.temperature,
        enforce_firewall=request.enforce_firewall,
        k_threshold=request.k_threshold,
    )


@router.post("/upload-benchmark", response_model=BenchmarkResponse)
async def upload_benchmark_endpoint(
    file: UploadFile = File(...),
    provider: str = "mock",
    model_name: str | None = None,
    temperature: float = 0.7,
    enforce_firewall: bool = False,
    k_threshold: int = 3,
) -> BenchmarkResponse:
    filename = file.filename or "upload"
    raw_bytes = await file.read()
    extracted_text, file_type = file_extractor.validate_and_extract(
        filename=filename,
        content_type=file.content_type or "",
        data=raw_bytes,
    )
    if len(extracted_text) > settings.MAX_PROMPT_LENGTH:
        extracted_text = extracted_text[: settings.MAX_PROMPT_LENGTH]
    return await _run_pipeline(
        prompt=extracted_text,
        provider=provider,
        model_name=model_name,
        temperature=temperature,
        enforce_firewall=enforce_firewall,
        k_threshold=k_threshold,
        file_info=FileInfo(
            filename=filename,
            file_type=file_type,
            size_bytes=len(raw_bytes),
            extracted_chars=len(extracted_text),
        ),
    )


@router.get("/providers")
async def list_providers() -> JSONResponse:
    return JSONResponse(content={"providers": llm_service.available_providers()})

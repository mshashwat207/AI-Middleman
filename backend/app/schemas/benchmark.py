from pydantic import BaseModel, Field
from typing import List, Optional


class BenchmarkRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=32000)
    provider: str = Field(default="groq")
    model_name: Optional[str] = Field(default=None)
    temperature: float = Field(default=0.7, ge=0.0, le=1.0)
    enforce_firewall: bool = Field(default=False)
    k_threshold: int = Field(default=3, ge=1, le=10)


class FirewallResult(BaseModel):
    passed: bool
    risk_score: float
    detected_patterns: List[str]


class IndirectPIIWarning(BaseModel):
    category: str
    snippet: str
    reason: str


class EntityDetail(BaseModel):
    entity_type: str
    real_value: str
    fake_value: str
    confidence: float


class MethodResult(BaseModel):
    method: str
    masked_payload: str
    llm_response: str
    final_unmasked_output: str
    entities_found: int
    entity_types: List[str]
    entity_table: List[EntityDetail]
    latency_ms: float
    utility_score: float
    utility_score_valid: bool
    response_length: int


class FileInfo(BaseModel):
    filename: str
    file_type: str
    size_bytes: int
    extracted_chars: int


class BenchmarkResponse(BaseModel):
    request_id: str
    original_prompt: str
    firewall: FirewallResult
    indirect_pii_warnings: List[IndirectPIIWarning]
    results: List[MethodResult]
    total_latency_ms: float
    file_info: Optional[FileInfo] = None
    prompt_length: int
    prompt_length_limit: int
    provider_used: str
    model_used: str
    is_simulated: bool

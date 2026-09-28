from sqlalchemy.orm import Session as DbSession
from app.models.audit import AuditLog
from typing import List, Optional

class AuditService:
    def log_request(
        self,
        db: DbSession,
        request_id: str,
        session_id: Optional[str],
        provider: str,
        model: Optional[str],
        pii_entity_count: int,
        entity_types: List[str],
        prompt_risk_score: float,
        blocked: bool,
        latency_ms: float,
        error_category: Optional[str] = None
    ) -> AuditLog:
        log_entry = AuditLog(
            request_id=request_id,
            session_id=session_id,
            provider=provider,
            model=model or "default",
            pii_entity_count=pii_entity_count,
            entity_types=",".join(set(entity_types)),
            prompt_risk_score=prompt_risk_score,
            blocked=blocked,
            latency_ms=latency_ms,
            error_category=error_category
        )
        db.add(log_entry)
        db.commit()
        return log_entry

audit_service = AuditService()

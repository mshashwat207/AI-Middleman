from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.models.database import get_db
from app.models.audit import AuditLog

router = APIRouter()


@router.get("/history")
def get_history(
    db: Session = Depends(get_db),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> JSONResponse:
    total = db.query(AuditLog).count()
    rows = (
        db.query(AuditLog)
        .order_by(AuditLog.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    entries = []
    for row in rows:
        entries.append({
            "request_id":       row.request_id,
            "created_at":       row.created_at.isoformat() if row.created_at else None,
            "provider":         row.provider,
            "model":            row.model,
            "pii_entity_count": row.pii_entity_count,
            "entity_types":     row.entity_types,
            "prompt_risk_score":row.prompt_risk_score,
            "blocked":          row.blocked,
            "latency_ms":       row.latency_ms,
            "error_category":   row.error_category,
        })

    return JSONResponse(content={
        "total":   total,
        "limit":   limit,
        "offset":  offset,
        "entries": entries,
    })

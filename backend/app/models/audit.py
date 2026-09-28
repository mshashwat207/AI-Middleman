from sqlalchemy import Column, String, Integer, DateTime, Boolean, Float, Text
from datetime import datetime, timezone
from app.models.database import Base
import uuid

def utcnow():
    return datetime.now(timezone.utc)

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    request_id = Column(String, index=True)
    session_id = Column(String, index=True)
    provider = Column(String)
    model = Column(String)
    pii_entity_count = Column(Integer)
    entity_types = Column(Text)  # comma separated
    prompt_risk_score = Column(Float)
    blocked = Column(Boolean)
    latency_ms = Column(Float)
    error_category = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)

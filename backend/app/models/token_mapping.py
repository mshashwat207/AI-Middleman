from sqlalchemy import Column, String, Integer, DateTime, Boolean, ForeignKey
from datetime import datetime, timezone
from app.models.database import Base
import uuid

def utcnow():
    return datetime.now(timezone.utc)

class Session(Base):
    __tablename__ = "sessions"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    created_at = Column(DateTime(timezone=True), default=utcnow)
    expires_at = Column(DateTime(timezone=True))
    status = Column(String, default="active")

class TokenMapping(Base):
    __tablename__ = "token_mappings"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, ForeignKey("sessions.id"), index=True)
    token = Column(String, index=True)  # e.g., [PERSON_1]
    encrypted_value = Column(String)    # encrypted original value
    entity_type = Column(String)        # e.g., PERSON
    created_at = Column(DateTime(timezone=True), default=utcnow)
    expires_at = Column(DateTime(timezone=True))

from cryptography.fernet import Fernet
from sqlalchemy.orm import Session as DbSession
from app.models.token_mapping import TokenMapping, Session as DbSessionModel
from app.core.config import settings
from datetime import datetime, timedelta, timezone
from typing import Optional
import logging

logger = logging.getLogger(__name__)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class TokenStoreService:
    def __init__(self) -> None:
        try:
            self.fernet = Fernet(settings.ENCRYPTION_KEY.encode("utf-8"))
        except Exception as exc:
            raise ValueError(
                "ENCRYPTION_KEY is invalid. Must be a 32-byte url-safe base64 key."
            ) from exc

    def purge_expired(self, db: DbSession) -> int:
        deleted = (
            db.query(TokenMapping)
            .filter(TokenMapping.expires_at <= utcnow())
            .delete(synchronize_session=False)
        )
        db.query(DbSessionModel).filter(
            DbSessionModel.expires_at <= utcnow()
        ).delete(synchronize_session=False)
        db.commit()
        if deleted:
            logger.info("Purged %d expired token mappings.", deleted)
        return deleted

    def encrypt_value(self, value: str) -> str:
        return self.fernet.encrypt(value.encode("utf-8")).decode("utf-8")

    def decrypt_value(self, encrypted_value: str) -> str:
        return self.fernet.decrypt(encrypted_value.encode("utf-8")).decode("utf-8")

    def get_or_create_session(
        self, db: DbSession, session_id: Optional[str] = None
    ) -> DbSessionModel:
        if session_id:
            db_session = (
                db.query(DbSessionModel)
                .filter(
                    DbSessionModel.id == session_id,
                    DbSessionModel.expires_at > utcnow(),
                )
                .first()
            )
            if db_session:
                return db_session

        expires_at = utcnow() + timedelta(minutes=settings.TOKEN_TTL_MINUTES)
        db_session = DbSessionModel(expires_at=expires_at)
        db.add(db_session)
        db.commit()
        db.refresh(db_session)
        return db_session

    def store_mapping(
        self,
        db: DbSession,
        session_id: str,
        token: str,
        value: str,
        entity_type: str,
    ) -> TokenMapping:
        encrypted_val = self.encrypt_value(value)
        expires_at = utcnow() + timedelta(minutes=settings.TOKEN_TTL_MINUTES)
        mapping = TokenMapping(
            session_id=session_id,
            token=token,
            encrypted_value=encrypted_val,
            entity_type=entity_type,
            expires_at=expires_at,
        )
        db.add(mapping)
        db.commit()
        db.refresh(mapping)
        return mapping

    def get_mapping(
        self, db: DbSession, session_id: str, token: str
    ) -> Optional[str]:
        mapping = (
            db.query(TokenMapping)
            .filter(
                TokenMapping.session_id == session_id,
                TokenMapping.token == token,
                TokenMapping.expires_at > utcnow(),
            )
            .first()
        )
        if not mapping:
            return None
        return self.decrypt_value(mapping.encrypted_value)


token_store = TokenStoreService()

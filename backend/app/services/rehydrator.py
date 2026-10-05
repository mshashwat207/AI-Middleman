from sqlalchemy.orm import Session as DbSession
from app.services.token_store import token_store
import re
import logging

logger = logging.getLogger(__name__)

_TOKEN_RE = re.compile(r"\[PII::[A-Z_]+::\d+::[0-9a-f]{8}\]")


class RehydratorService:
    def rehydrate(self, db: DbSession, masked_text: str, session_id: str) -> str:
        def replacer(match: re.Match) -> str:
            token_full = match.group(0)
            decrypted_value = token_store.get_mapping(db, session_id, token_full)
            if decrypted_value is not None:
                return decrypted_value
            logger.warning(
                "Token %s found in LLM response but no mapping exists for session.",
                token_full,
            )
            return token_full

        return _TOKEN_RE.sub(replacer, masked_text)


rehydrator_service = RehydratorService()

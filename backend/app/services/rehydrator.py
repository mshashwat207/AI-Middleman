from sqlalchemy.orm import Session as DbSession
from app.services.token_store import token_store
import re
import logging

logger = logging.getLogger(__name__)

class RehydratorService:
    def __init__(self):
        # Matches our token pattern, e.g., [PERSON_1], [EMAIL_2]
        self.token_pattern = re.compile(r"\[([A-Z_]+_\d+)\]")

    def rehydrate(self, db: DbSession, masked_text: str, session_id: str) -> str:
        """
        Scans masked_text for tokens and replaces them with original decrypted values
        if they exist in the given session's token mappings.
        """
        def replacer(match):
            token_inner = match.group(1)
            token_full = f"[{token_inner}]"
            
            # Fetch from DB / token store
            decrypted_value = token_store.get_mapping(db, session_id, token_full)
            if decrypted_value is not None:
                return decrypted_value
            else:
                # If we don't have it, don't replace it (could be something the model generated itself)
                logger.warning(f"Found token {token_full} in LLM response but no mapping exists for session {session_id}")
                return token_full

        rehydrated_text = self.token_pattern.sub(replacer, masked_text)
        return rehydrated_text

rehydrator_service = RehydratorService()

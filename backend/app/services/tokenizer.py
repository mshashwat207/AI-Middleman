from typing import List, Tuple, Dict
from app.schemas.masking import DetectedEntity, MaskedEntityPreview
from app.services.token_store import token_store
from sqlalchemy.orm import Session as DbSession
import uuid
import logging

logger = logging.getLogger(__name__)

_NS = "PII"


def _make_token(entity_type: str, counter: int, slug: str) -> str:
    return f"[{_NS}::{entity_type}::{counter}::{slug}]"


class TokenizerService:
    def tokenize(
        self,
        db: DbSession,
        text: str,
        entities: List[DetectedEntity],
        session_id: str,
    ) -> Tuple[str, List[MaskedEntityPreview]]:
        sorted_entities = sorted(entities, key=lambda x: x.start, reverse=True)

        value_to_token: Dict[str, str] = {}
        type_counters: Dict[str, int] = {}

        from app.models.token_mapping import TokenMapping

        existing_mappings = (
            db.query(TokenMapping)
            .filter(TokenMapping.session_id == session_id)
            .all()
        )
        for mapping in existing_mappings:
            try:
                decrypted_val = token_store.decrypt_value(mapping.encrypted_value)
                value_to_token[decrypted_val] = mapping.token
                parts = mapping.token.strip("[]").split("::")
                if len(parts) == 4 and parts[2].isdigit():
                    etype = parts[1]
                    type_counters[etype] = max(
                        type_counters.get(etype, 0), int(parts[2])
                    )
            except Exception as exc:
                logger.error("Failed to decrypt existing mapping: %s", exc)

        masked_text = text
        previews: List[MaskedEntityPreview] = []

        for entity in sorted_entities:
            if entity.value in value_to_token:
                token = value_to_token[entity.value]
            else:
                count = type_counters.get(entity.entity_type, 0) + 1
                type_counters[entity.entity_type] = count
                slug = uuid.uuid4().hex[:8]
                token = _make_token(entity.entity_type, count, slug)
                value_to_token[entity.value] = token
                token_store.store_mapping(
                    db=db,
                    session_id=session_id,
                    token=token,
                    value=entity.value,
                    entity_type=entity.entity_type,
                )

            masked_text = masked_text[: entity.start] + token + masked_text[entity.end :]
            previews.append(
                MaskedEntityPreview(
                    type=entity.entity_type,
                    token=token,
                    confidence=entity.confidence,
                )
            )

        previews.reverse()
        return masked_text, previews


tokenizer_service = TokenizerService()

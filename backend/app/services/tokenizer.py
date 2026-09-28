from typing import List, Tuple, Dict
from app.schemas.masking import DetectedEntity, MaskedEntityPreview
from app.services.token_store import token_store
from sqlalchemy.orm import Session as DbSession
import logging

logger = logging.getLogger(__name__)

class TokenizerService:
    
    def tokenize(self, db: DbSession, text: str, entities: List[DetectedEntity], session_id: str) -> Tuple[str, List[MaskedEntityPreview]]:
        """
        Replaces entities in text with deterministic tokens and stores the mapping.
        Returns the masked text and a list of token previews.
        """
        # Sort entities by start position in reverse so we can replace from back to front
        # without messing up the string indices.
        sorted_entities = sorted(entities, key=lambda x: x.start, reverse=True)
        
        # State tracking for deterministic tokenization within this request
        # mapping raw value to token
        value_to_token: Dict[str, str] = {}
        type_counters: Dict[str, int] = {}
        
        masked_text = text
        previews = []
        
        # In a real distributed system, we'd want to also check the DB for existing mappings
        # for this session_id to maintain consistency across multiple requests in the same session.
        # For simplicity here, we'll fetch existing mappings for this session first.
        # Actually, let's just make it consistent within the current request, 
        # or we could fetch all session mappings. Let's fetch session mappings to keep it stable.
        from app.models.token_mapping import TokenMapping
        existing_mappings = db.query(TokenMapping).filter(TokenMapping.session_id == session_id).all()
        for mapping in existing_mappings:
            try:
                decrypted_val = token_store.decrypt_value(mapping.encrypted_value)
                value_to_token[decrypted_val] = mapping.token
                
                # Update counters based on highest seen
                # token format: [TYPE_X]
                if mapping.token.startswith("[") and mapping.token.endswith("]"):
                    inner = mapping.token[1:-1]
                    if "_" in inner:
                        etype, num = inner.rsplit("_", 1)
                        if num.isdigit():
                            type_counters[etype] = max(type_counters.get(etype, 0), int(num))
            except Exception as e:
                logger.error(f"Error decrypting existing mapping: {e}")
        
        for entity in sorted_entities:
            # Check if we already have a token for this exact value
            if entity.value in value_to_token:
                token = value_to_token[entity.value]
            else:
                # Generate new token
                count = type_counters.get(entity.entity_type, 0) + 1
                type_counters[entity.entity_type] = count
                token = f"[{entity.entity_type}_{count}]"
                
                value_to_token[entity.value] = token
                
                # Store it securely
                token_store.store_mapping(
                    db=db, 
                    session_id=session_id, 
                    token=token, 
                    value=entity.value, 
                    entity_type=entity.entity_type
                )
            
            # Replace in text
            masked_text = masked_text[:entity.start] + token + masked_text[entity.end:]
            
            # Add to previews
            previews.append(MaskedEntityPreview(
                type=entity.entity_type,
                token=token,
                confidence=entity.confidence
            ))
            
        # Reverse previews so they are in natural order
        previews.reverse()
        return masked_text, previews

tokenizer_service = TokenizerService()

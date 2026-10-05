import logging
from typing import List
from sentence_transformers import SentenceTransformer, util
import torch

logger = logging.getLogger(__name__)

_model = None


def _get_model():
    global _model
    if _model is None:
        try:
            logger.info("SemanticScorer loading all-MiniLM-L6-v2...")
            # Using a fast, highly capable contextual embedding model
            _model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("SemanticScorer loaded all-MiniLM-L6-v2.")
        except Exception as e:
            logger.error("Failed to load sentence-transformers model: %s", e)
    return _model


class SemanticScorer:
    def score(self, reference: str, candidate: str) -> float:
        if not reference.strip() or not candidate.strip():
            return 0.0
        try:
            model = _get_model()
            if model is None:
                return 0.0
            
            # Encode sentences to get their embeddings
            embeddings1 = model.encode(reference[:100000], convert_to_tensor=True)
            embeddings2 = model.encode(candidate[:100000], convert_to_tensor=True)
            
            # Compute cosine-similarities
            cosine_score = util.cos_sim(embeddings1, embeddings2).item()
            
            return round(float(max(0.0, min(1.0, cosine_score))), 4)
        except Exception as exc:
            logger.error("Semantic scoring failed: %s", exc)
            return 0.0

    def score_against_prompt(self, original_prompt: str, responses: List[str]) -> List[float]:
        return [self.score(original_prompt, r) for r in responses]


semantic_scorer = SemanticScorer()


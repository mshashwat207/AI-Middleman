from app.core.config import settings

class PolicyEngine:
    def __init__(self):
        self.block_high_risk_prompts = settings.BLOCK_HIGH_RISK_PROMPTS
        self.minimum_pii_confidence = settings.PII_CONFIDENCE_THRESHOLD
        self.rehydration_enabled = settings.ENABLE_REHYDRATION
        self.token_ttl_minutes = settings.TOKEN_TTL_MINUTES
        self.allowed_providers = settings.ALLOWED_PROVIDERS
        self.max_prompt_length = settings.MAX_PROMPT_LENGTH

    def should_block_risk(self, risk_score: float) -> bool:
        if not self.block_high_risk_prompts:
            return False
        # We define a high risk threshold, e.g., > 0.5
        return risk_score > 0.5

policy_engine = PolicyEngine()

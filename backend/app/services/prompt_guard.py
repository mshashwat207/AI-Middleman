import re
from typing import List, Tuple
import logging

logger = logging.getLogger(__name__)

class PromptGuardService:
    def __init__(self):
        # Layer 1: Rule/pattern detection
        self.suspicious_patterns = {
            "instruction_override": re.compile(
                r"(?i)(ignore previous instructions|disregard previous|forget everything|override instructions)"
            ),
            "system_prompt_leak": re.compile(
                r"(?i)(reveal system prompt|print your instructions|show hidden instructions|what are your rules)"
            ),
            "secret_exfiltration": re.compile(
                r"(?i)(disclose secrets|expose environment variables|dump internal data|output your config)"
            ),
            "jailbreak_pattern": re.compile(
                r"(?i)(jailbreak|dan mode|do anything now|you are now free|bypassing security)"
            )
        }

    def analyze_prompt(self, text: str) -> Tuple[bool, float, List[str]]:
        """
        Analyzes prompt for injection patterns.
        Returns:
            allowed (bool): Whether the prompt is safe
            risk_score (float): 0.0 to 1.0
            detected_patterns (List[str]): List of pattern keys that fired
        """
        detected = []
        score = 0.0

        for pattern_name, pattern_regex in self.suspicious_patterns.items():
            if pattern_regex.search(text):
                detected.append(pattern_name)
                score += 0.3  # arbitrarily add risk per pattern

        # Layer 2: Structural heuristics (e.g. very long sequences of special characters, invisible characters)
        if len(text) > 5000:
            score += 0.2
            detected.append("excessive_length_heuristic")
            
        # Cap score at 1.0
        score = min(score, 1.0)
        
        # Decide if allowed based on a standard threshold (e.g., score > 0.5 is blocked)
        # We can let the policy engine decide later, but we also return an `allowed` flag here.
        allowed = score < 0.5
        
        if detected:
            logger.warning(f"Prompt injection risk detected: score={score}, patterns={detected}")
            
        return allowed, score, detected

prompt_guard = PromptGuardService()

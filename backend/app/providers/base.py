from abc import ABC, abstractmethod
from typing import List, Dict, Any

class LLMProvider(ABC):
    @abstractmethod
    async def generate(self, messages: List[Dict[str, str]], model: str, temperature: float, **kwargs) -> str:
        """
        Generate response from the LLM.
        messages: List of dicts with 'role' and 'content' keys.
        """
        pass

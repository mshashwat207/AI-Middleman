from typing import List, Dict, Any
from app.providers.base import LLMProvider
import asyncio

class MockProvider(LLMProvider):
    async def generate(self, messages: List[Dict[str, str]], model: str, temperature: float, **kwargs) -> str:
        # Simulate network latency
        await asyncio.sleep(0.5)
        
        last_message = messages[-1]["content"] if messages else ""
        
        # We just echo back the content with a mock prefix, 
        # so we can test that the tokens survived the trip to the LLM.
        return f"Mock Response: Received prompt '{last_message}'"


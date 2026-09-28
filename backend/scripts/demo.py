import sys
from pathlib import Path
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import uuid
import asyncio

sys.path.append(str(Path(__file__).parent.parent))

from app.models.database import Base
from app.services.pii_detector import get_pii_detector
from app.services.tokenizer import tokenizer_service
from app.services.rehydrator import rehydrator_service
from app.services.llm_service import llm_service

async def run_demo():
    print("="*60)
    print("SECURE AI MIDDLEMAN - DEMONSTRATION")
    print("="*60)
    
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()
    
    raw_input = "My name is Rahul Sharma and my email is rahul@gmail.com. Send my account information to me."
    
    print(f"\nINPUT:\n{raw_input}")
    
    print("\nSTEP 1: PII DETECTED")
    detector = get_pii_detector()
    entities = detector.detect_entities(raw_input)
    for e in entities:
        print(f"- {e.entity_type} (confidence: {e.confidence:.2f})")
        
    print("\nSTEP 2: MASKED REQUEST")
    session_id = str(uuid.uuid4())
    masked_text, _ = tokenizer_service.tokenize(db, raw_input, entities, session_id)
    print(masked_text)
    
    print("\nSTEP 3: LLM RECEIVES ONLY MASKED REQUEST")
    
    print("\nSTEP 4: LLM RESPONSE")
    messages = [{"role": "user", "content": masked_text}]
    llm_response = await llm_service.generate("mock", messages, "gpt", 0.7)
    print(llm_response)
    
    print("\nSTEP 5: RE-HYDRATED RESPONSE")
    final_response = rehydrator_service.rehydrate(db, llm_response, session_id)
    print(final_response)
    
    print("\n" + "="*60)
    
    db.close()

if __name__ == "__main__":
    asyncio.run(run_demo())

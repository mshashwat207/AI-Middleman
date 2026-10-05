# VUL-LLM Backend

FastAPI backend for the VUL-LLM PII masking benchmark.

## Quick start

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m spacy download en_core_web_lg
cp .env.example .env
# Add GROQ_API_KEY or GEMINI_API_KEY to .env
python scripts/init_db.py
uvicorn app.main:app --reload
```

## Environment variables

| Variable | Required | Description |
|---|---|---|
| ENCRYPTION_KEY | Recommended | Fernet key. Auto-generated if blank (tokens lost on restart). |
| GROQ_API_KEY | One of these | Free at console.groq.com |
| GEMINI_API_KEY | One of these | Free at aistudio.google.com |
| OPENAI_API_KEY | Optional | Paid |
| ANTHROPIC_API_KEY | Optional | Paid |
| DEFAULT_LLM_PROVIDER | No | mock / groq / gemini / openai / anthropic |
| GROQ_MODEL | No | Default: llama-3.1-8b-instant |
| GEMINI_MODEL | No | Default: gemini-1.5-flash |
| PII_CONFIDENCE_THRESHOLD | No | 0.0-1.0, default 0.65 |
| LLM_TIMEOUT_SECONDS | No | Default: 30 |

Generate an encryption key:
```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

## Project structure

```
app/
  core/config.py              Settings from .env
  api/routes/
    benchmark.py              POST /api/benchmark, POST /api/upload-benchmark
    history.py                GET /api/history
    chat.py                   POST /api/v1/chat
    security.py               POST /api/v1/security/mask|analyze
    health.py                 GET /health
  services/
    pii_detector.py           Presidio + custom Indian NER (Aadhaar, PAN, phone)
    indirect_pii_detector.py  Local contextual identity detection (no LLM)
    comparative_engine.py     3 masking methods
    prompt_guard.py           Injection firewall
    semantic_scorer.py        Cosine similarity via spaCy vectors
    llm_service.py            Provider dispatcher
    token_store.py            Fernet-encrypted token persistence
    rehydrator.py             Token-to-value restoration
    file_extractor.py         PDF, DOCX, TXT, image OCR extraction
  providers/
    groq_provider.py
    gemini_provider.py
    openai_provider.py
    anthropic_provider.py
    mock_provider.py
  models/
    audit.py                  AuditLog SQLAlchemy model
    token_mapping.py          Session + TokenMapping models
    database.py               SQLAlchemy engine
```

## Running tests

```bash
pytest tests/ -v
```

## Supported Groq models (free)

| Model | Context | Best for |
|---|---|---|
| llama-3.1-8b-instant | 128k | Default, fast |
| llama-3.3-70b-versatile | 128k | Best quality |
| mixtral-8x7b-32768 | 32k | Long documents |
| gemma2-9b-it | 8k | Google model |
| llama3-70b-8192 | 8k | Llama 3 base |

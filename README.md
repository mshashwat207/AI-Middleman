# VUL-LLM: LLM Privacy & Utility Benchmarking Engine

VUL-LLM is a robust, edge-deployable research environment designed to benchmark Personally Identifiable Information (PII) masking strategies for Large Language Models (LLMs). It measures the precise degradation of semantic utility across different anonymization architectures, empowering organizations to deploy zero-trust AI pipelines without sacrificing contextual reasoning.

## System Architecture

VUL-LLM intercepts sensitive prompts, sanitizes them via a localized K-Anonymity Heuristic Firewall, and processes them through three parallel masking pipelines.

```text
Raw Prompt
    |
    +-- Prompt Injection Firewall (Regex + Unicode Normalization)
    |
    +-- Direct PII Detection (Presidio + spaCy + Custom Regex)
    |
    +-- Indirect PII Detection (K-Anonymity Heuristic Firewall)
    |
    +-------+-------+-------+
    |       |       |       |
[REDACTED]  |    <PERSON_1> |   Fake Name       <-- 3 Parallel Masking Pipelines
    |       |       |       |
    +-------+-------+-------+
    |
   LLM Inference (Gemini, Groq, OpenAI, Anthropic)
    |
   Detokenization (Reverse-Mapping)
    |
   Semantic Utility Scoring (Cosine Similarity via Sentence-Transformers)
```

## Key Capabilities

1. **Tripartite Benchmarking Pipeline:**
   * **Hard Redaction:** Replaces entities directly with `[REDACTED]`. Guarantees privacy at the expense of attention-mechanism context.
   * **Categorical Tokenization:** Replaces entities with abstract, type-safe tags (e.g., `<PERSON_1>`). Preserves syntactic structure while neutralizing the Hyper-Realism Safety Trap.
   * **Synthetic Swapping:** Replaces entities with realistic, localized fake data generated dynamically via the `Faker` engine.

2. **K-Anonymity Heuristic Firewall:**
   Protects against the **Mosaic Effect** deanonymization without relying on API-driven "LLM-as-a-Judge" architectures. It locally calculates the density of quasi-identifiers (e.g., Age + Gender + Role + Location). A dynamic threshold slider enables real-time adjustments, and an enforcement toggle issues a strict HTTP 403 computational block if the user-defined $k$ threshold is breached (default $k=3$).

3. **Custom Localization Heuristics:**
   Features aggressive regex recognizers to supplement statistical NLP models, ensuring 100% detection of regional formats such as Indian DD/MM/YYYY dates, Aadhaar, PAN, and local address structures.

## Installation and Setup

### Backend Deployment

```bash
cd backend
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m spacy download en_core_web_lg
cp .env.example .env
```
*Configure `.env` with your API keys (e.g., `GEMINI_API_KEY`, `GROQ_API_KEY`).*

```bash
python scripts/init_db.py
uvicorn app.main:app --port 8000
```

### Frontend Deployment

```bash
cd frontend
npm install
npm run dev
```
Access the dashboard at `http://localhost:5173`.

### Docker Deployment (Alternative)

```bash
cd backend
docker compose up --build
```

## Batch Processing for Academic Research

For researchers aggregating data across large corpuses, VUL-LLM includes a specialized CLI batch processor that handles LLM API rate limits and outputs deterministic utility scores:

```bash
# Ensure you have activated your backend virtual environment first
source backend/.venv/bin/activate

# Run the batch processor against a CSV dataset
python batch_benchmark.py my_dataset.csv --output results.json --provider gemini --enforce-firewall --k-threshold 3
```

## API Reference

| Method | Path | Description |
|---|---|---|
| POST | /api/benchmark | Execute 3-way benchmarking pipeline on text payload |
| POST | /api/upload-benchmark | Execute benchmarking on uploaded documents (PDF, DOCX) |
| GET | /api/providers | Retrieve configured LLM providers |
| GET | /api/history | Fetch audit logs for past benchmark requests |
| POST | /api/v1/chat | Standard single-pipeline privacy proxy |
| POST | /api/v1/security/mask | Preview masking outputs without LLM execution |
| POST | /api/v1/security/analyze | Execute local PII and injection risk analysis |

## Security & Privacy Guarantees

* **Zero-Trust Transmission:** Raw PII never leaves the local environment. Only mathematically masked payloads are transmitted to external AI providers.
* **Ephemeral Storage:** Token mappings are stored temporarily in memory and encrypted at rest using Fernet (AES-128-CBC). Tokens expire automatically after 30 minutes.
* **Rate Limiting:** Built-in throttling at 60 requests per minute per IP to prevent API exhaustion.
* **Injection Defense:** The firewall blocks 5 distinct pattern families, including zero-width spaces and Unicode homoglyph attacks.

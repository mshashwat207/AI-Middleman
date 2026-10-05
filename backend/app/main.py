from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.core.config import settings
from app.models.database import Base, engine, SessionLocal
from app.middleware.request_security import RequestSecurityMiddleware
from app.api.routes import health, chat, security, benchmark, history
from app.services.token_store import token_store
from app.services.pii_detector import get_pii_detector
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)

Base.metadata.create_all(bind=engine)

limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])

_docs_url    = None if settings.APP_ENV == "production" else "/docs"
_redoc_url   = None if settings.APP_ENV == "production" else "/redoc"
_openapi_url = None if settings.APP_ENV == "production" else "/openapi.json"

app = FastAPI(
    title="VUL-LLM",
    description="PII masking benchmark: measures semantic utility cost of three privacy methods.",
    version="2.1.0",
    docs_url=_docs_url,
    redoc_url=_redoc_url,
    openapi_url=_openapi_url,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["POST", "GET", "OPTIONS"],
    allow_headers=["Content-Type", "Accept"],
)

app.add_middleware(RequestSecurityMiddleware, max_content_length=65536)

app.include_router(health.router,     tags=["Health"])
app.include_router(chat.router,       prefix="/api/v1",          tags=["Chat"])
app.include_router(security.router,   prefix="/api/v1/security", tags=["Security"])
app.include_router(benchmark.router,  prefix="/api",             tags=["Benchmark"])
app.include_router(history.router,    prefix="/api",             tags=["History"])


@app.on_event("startup")
def _on_startup():
    db = SessionLocal()
    try:
        purged = token_store.purge_expired(db)
        logger.info("Startup: purged %d expired token mappings.", purged)
        logger.info("Startup: Pre-loading PII Detector (Presidio & spaCy)...")
        get_pii_detector()
        logger.info("Startup: PII Detector loaded successfully.")
    finally:
        db.close()


from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

if os.path.exists("frontend/dist"):
    app.mount("/", StaticFiles(directory="frontend/dist", html=True), name="static")

    @app.exception_handler(404)
    async def custom_404_handler(request: Request, exc):
        if request.url.path.startswith("/api"):
            return JSONResponse({"detail": "Not Found"}, status_code=404)
        return FileResponse("frontend/dist/index.html")
else:
    @app.get("/")
    def root():
        return {"service": "VUL-LLM", "version": "2.1.0", "status": "running (No frontend found)"}

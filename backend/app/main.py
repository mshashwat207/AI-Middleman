from fastapi import FastAPI
from app.api.routes import health, chat, security
from app.models.database import Base, engine

# Create tables for SQLite locally
Base.metadata.create_all(bind=engine)

from fastapi.middleware.cors import CORSMiddleware
from app.middleware.request_security import RequestSecurityMiddleware

app = FastAPI(
    title="Secure AI Middleman",
    description="Privacy-first middleware/proxy between users and external LLM APIs.",
    version="1.0.0"
)

# CORS Hardening
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For local demo, restrict in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request Size Limit and Secure Headers
app.add_middleware(RequestSecurityMiddleware, max_content_length=100000)

app.include_router(health.router, tags=["Health"])
app.include_router(chat.router, prefix="/api/v1", tags=["Chat"])
app.include_router(security.router, prefix="/api/v1/security", tags=["Security"])

@app.get("/")
def root():
    return {"message": "Welcome to the Secure AI Middleman API"}

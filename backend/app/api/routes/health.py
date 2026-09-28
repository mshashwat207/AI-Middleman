from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.models.database import get_db
from sqlalchemy import text

router = APIRouter()

@router.get("/health")
def health_check():
    return {"status": "ok"}

@router.get("/health/ready")
def health_ready(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception:
        db_status = "error"
    
    return {
        "status": "ready" if db_status == "ok" else "error",
        "database": db_status
    }

@router.get("/health/live")
def health_live():
    return {"status": "live"}

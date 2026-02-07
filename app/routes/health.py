from fastapi import APIRouter
from sqlalchemy import text
from app.config.database import SessionLocal

router = APIRouter()


@router.get("/")
async def test_db():
    """Test database connection"""
    db = SessionLocal()
    try:
        result = db.execute(text("SELECT 1")).scalar()
        return {"status": "DB OK", "result": result}
    finally:
        db.close()


@router.get("/health")
async def health() -> dict:
    """Health check endpoint"""
    print("[INFO] Health check endpoint accessed")
    return {"status": "ok"}

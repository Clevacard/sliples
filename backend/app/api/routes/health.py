"""Health check endpoint."""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
import redis

from app.database import get_db
from app.config import get_settings

router = APIRouter()
settings = get_settings()


@router.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """
    Health check endpoint.

    Returns the health status of the API and its dependencies:
    - database: PostgreSQL connection status
    - redis: Redis connection status
    """
    health = {
        "status": "healthy",
        "database": "disconnected",
        "redis": "disconnected",
    }

    # Check database
    try:
        db.execute(text("SELECT 1"))
        health["database"] = "connected"
    except Exception as e:
        health["status"] = "degraded"
        health["database_error"] = str(e)

    # Check Redis
    try:
        r = redis.from_url(settings.redis_url)
        r.ping()
        health["redis"] = "connected"
    except Exception as e:
        health["status"] = "degraded"
        health["redis_error"] = str(e)

    return health

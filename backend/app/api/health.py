from typing import Any, Dict
from fastapi import APIRouter, Response, status
from sqlalchemy import text

from ..config import settings
from ..db_session import engine
from ..services.realtime import check_redis_health

router = APIRouter()


@router.get("", response_model=Dict[str, Any])
@router.get("/", response_model=Dict[str, Any])
async def health_liveness() -> Dict[str, Any]:
    return {
        "status": "LIVE",
        "app": settings.APP_NAME,
        "environment": settings.ENVIRONMENT,
    }


@router.get("/ready", response_model=Dict[str, Any])
async def health_readiness(response: Response) -> Dict[str, Any]:
    checks = {
        "database": False,
        "redis": False,
    }
    
    # Check Database
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        checks["database"] = True
    except Exception as err:
        checks["database_error"] = str(err)

    # Check Redis
    redis_healthy = await check_redis_health()
    checks["redis"] = redis_healthy
    if not redis_healthy:
        checks["redis_note"] = "Running in local fallback mode"

    # In production, if Redis is configured, require both DB and Redis
    if settings.ENVIRONMENT == "production" and settings.REDIS_URL:
        is_ready = checks["database"] and checks["redis"]
    else:
        is_ready = checks["database"]

    if not is_ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return {
        "status": "READY" if is_ready else "NOT_READY",
        "checks": checks,
    }

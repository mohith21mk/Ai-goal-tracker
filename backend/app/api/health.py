from typing import Any, Dict
from fastapi import APIRouter, Response, status
from sqlalchemy import text

from ..config import settings
from ..db_session import engine
from ..services.realtime import get_redis_client

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
    try:
        redis_cli = get_redis_client()
        if redis_cli:
            checks["redis"] = True
        else:
            checks["redis"] = False
            checks["redis_note"] = "Running in fallback mode"
    except Exception as err:
        checks["redis"] = False
        checks["redis_error"] = str(err)

    is_ready = checks["database"]
    if not is_ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return {
        "status": "READY" if is_ready else "NOT_READY",
        "checks": checks,
    }

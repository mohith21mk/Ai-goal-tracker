from typing import Any, Dict
from fastapi import APIRouter, HTTPException

from ..services.reflection import generate_daily_reflection

router = APIRouter()


@router.get("/daily", response_model=Dict[str, Any])
async def get_daily_reflection() -> Dict[str, Any]:
    try:
        data = generate_daily_reflection()
        return data
    except Exception as err:
        raise HTTPException(status_code=500, detail=f"Failed to generate daily reflection: {err}")

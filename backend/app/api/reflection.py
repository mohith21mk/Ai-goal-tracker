from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException

from ..services.reflection import generate_daily_reflection
from .auth import get_current_user

router = APIRouter()


@router.get("/daily", response_model=Dict[str, Any])
async def get_daily_reflection(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    try:
        user_id = current_user["id"]
        data = generate_daily_reflection(user_id)
        return data
    except Exception as err:
        raise HTTPException(status_code=500, detail=f"Failed to generate daily reflection: {err}")

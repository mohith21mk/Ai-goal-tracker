from typing import Any, Dict
from fastapi import APIRouter, Depends

from .auth import get_current_user
from ..services.progression import get_user_progression

router = APIRouter()


@router.get("", response_model=Dict[str, Any])
async def get_progression_endpoint(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get server-authoritative progression (XP, Level, Rank, Progress %) for the current user.
    """
    user_id = current_user["id"]
    return get_user_progression(user_id)

from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException

from .auth import get_current_user
from ..database import get_connection
from ..services.progression import (
    evaluate_and_issue_credentials,
    list_user_credentials,
)

router = APIRouter()


@router.get("", response_model=List[Dict[str, Any]])
async def get_my_credentials(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """
    Get all credentials earned by the current authenticated user.
    """
    user_id = current_user["id"]
    return list_user_credentials(user_id)


@router.get("/user/{user_id}", response_model=List[Dict[str, Any]])
async def get_user_public_credentials(
    user_id: int
) -> List[Dict[str, Any]]:
    """
    Get public credentials earned by a specific user.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return list_user_credentials(user_id)


@router.post("/check", response_model=Dict[str, Any])
async def check_and_issue_credentials(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Evaluate server-authoritative evidence and issue any newly earned credentials.
    Anti-spoofing: Does not accept client claims; calculates strictly from DB records.
    """
    user_id = current_user["id"]
    result = evaluate_and_issue_credentials(user_id)
    return result

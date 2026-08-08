from typing import Any, Dict

from fastapi import APIRouter, HTTPException

from ..database import get_connection

router = APIRouter()


@router.get("", response_model=Dict[str, Any])
async def get_current_user() -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", ("demo@masterykeycoach.com",))
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Development demo user not found")

    user_dict = dict(row)
    user_dict["is_active"] = True
    return user_dict

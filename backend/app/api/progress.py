from typing import Any, Dict

from fastapi import APIRouter

from ..database import get_connection

router = APIRouter()


@router.get("", response_model=Dict[str, Any])
async def get_progress() -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM missions")
    total = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM missions WHERE completed = 1")
    completed = cursor.fetchone()[0]

    conn.close()

    percentage = round((completed / total) * 100) if total > 0 else 0

    return {
        "completed": completed,
        "total": total,
        "percentage": percentage,
    }

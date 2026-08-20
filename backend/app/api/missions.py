from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ..database import get_connection
from .auth import get_current_user

router = APIRouter()


class MissionCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = ""
    category: Optional[str] = "general"
    time: Optional[str] = "15 min"
    difficulty: Optional[str] = "easy"
    xp_reward: Optional[int] = 10


def format_mission_row(row: Any) -> Dict[str, Any]:
    mission_dict = dict(row)
    mission_dict["completed"] = bool(mission_dict["completed"])
    return mission_dict


@router.get("", response_model=List[Dict[str, Any]])
async def list_missions(current_user: Dict[str, Any] = Depends(get_current_user)) -> List[Dict[str, Any]]:
    user_id = current_user["id"]
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM missions WHERE user_id = ? ORDER BY id ASC", (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return [format_mission_row(row) for row in rows]


@router.post("", response_model=Dict[str, Any])
async def create_mission(
    mission_in: MissionCreateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    user_id = current_user["id"]
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO missions (user_id, title, description, category, time, difficulty, xp_reward, completed)
        VALUES (?, ?, ?, ?, ?, ?, ?, 0)
        """,
        (
            user_id,
            mission_in.title,
            mission_in.description,
            mission_in.category or "general",
            mission_in.time or "15 min",
            mission_in.difficulty or "easy",
            mission_in.xp_reward or 10,
        ),
    )
    conn.commit()
    mission_id = cursor.lastrowid
    cursor.execute("SELECT * FROM missions WHERE id = ?", (mission_id,))
    row = cursor.fetchone()
    conn.close()
    return format_mission_row(row)


@router.patch("/{mission_id}/toggle", response_model=Dict[str, Any])
async def toggle_mission(
    mission_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    user_id = current_user["id"]
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM missions WHERE id = ? AND user_id = ?", (mission_id, user_id))
    row = cursor.fetchone()

    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail=f"Mission with ID {mission_id} not found")

    new_completed = 0 if row["completed"] else 1
    if new_completed == 1:
        cursor.execute(
            "UPDATE missions SET completed = 1, completed_at = CURRENT_TIMESTAMP WHERE id = ? AND user_id = ?",
            (mission_id, user_id),
        )
    else:
        cursor.execute(
            "UPDATE missions SET completed = 0, completed_at = NULL WHERE id = ? AND user_id = ?",
            (mission_id, user_id),
        )
    conn.commit()

    cursor.execute("SELECT * FROM missions WHERE id = ?", (mission_id,))
    updated_row = cursor.fetchone()
    conn.close()
    return format_mission_row(updated_row)

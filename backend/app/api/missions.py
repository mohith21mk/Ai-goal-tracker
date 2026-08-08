from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..database import get_connection

router = APIRouter()


class MissionCreateRequest(BaseModel):
    title: str
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
async def list_missions() -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM missions ORDER BY id ASC")
    rows = cursor.fetchall()
    conn.close()
    return [format_mission_row(row) for row in rows]


@router.post("", response_model=Dict[str, Any])
async def create_mission(mission_in: MissionCreateRequest) -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO missions (title, description, category, time, difficulty, xp_reward, completed)
        VALUES (?, ?, ?, ?, ?, ?, 0)
        """,
        (
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
async def toggle_mission(mission_id: int) -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM missions WHERE id = ?", (mission_id,))
    row = cursor.fetchone()

    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail=f"Mission with ID {mission_id} not found")

    new_completed = 0 if row["completed"] else 1
    if new_completed == 1:
        cursor.execute(
            "UPDATE missions SET completed = 1, completed_at = CURRENT_TIMESTAMP WHERE id = ?",
            (mission_id,),
        )
    else:
        cursor.execute(
            "UPDATE missions SET completed = 0, completed_at = NULL WHERE id = ?",
            (mission_id,),
        )
    conn.commit()

    cursor.execute("SELECT * FROM missions WHERE id = ?", (mission_id,))
    updated_row = cursor.fetchone()
    conn.close()
    return format_mission_row(updated_row)

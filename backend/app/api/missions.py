from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
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


def format_mission_row(row: Any, is_completed_today: bool = False) -> Dict[str, Any]:
    mission_dict = dict(row)
    mission_dict["completed"] = bool(is_completed_today)
    mission_dict["completed_today"] = bool(is_completed_today)
    mission_dict["last_completed_at"] = row["completed_at"] if "completed_at" in mission_dict else None
    return mission_dict


@router.get("", response_model=List[Dict[str, Any]])
async def list_missions(
    target_date: Optional[str] = Query(None, description="Optional YYYY-MM-DD to check completion status"),
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> List[Dict[str, Any]]:
    """
    List user missions with automatic daily checklist reset.
    A mission is marked 'completed: true' ONLY if it was completed on target_date (default: today).
    When a new day begins, the checklist automatically resets to unchecked.
    """
    user_id = current_user["id"]
    today_str = target_date if target_date else datetime.now(timezone.utc).strftime("%Y-%m-%d")

    conn = get_connection()
    cursor = conn.cursor()

    # 1. Fetch all user missions
    cursor.execute("SELECT * FROM missions WHERE user_id = ? ORDER BY id ASC", (user_id,))
    rows = cursor.fetchall()

    # 2. Fetch all mission IDs completed on target_date
    cursor.execute(
        "SELECT mission_id FROM mission_logs WHERE user_id = ? AND completed_date = ?",
        (user_id, today_str),
    )
    completed_today_ids = {r["mission_id"] for r in cursor.fetchall()}

    # Check if user has any mission_logs at all
    cursor.execute("SELECT COUNT(*) FROM mission_logs WHERE user_id = ?", (user_id,))
    has_logs = (cursor.fetchone()[0] or 0) > 0

    conn.close()

    result = []
    for row in rows:
        m_id = row["id"]
        if has_logs:
            completed_today = (m_id in completed_today_ids)
        else:
            completed_today = bool(row["completed"]) and bool(row["completed_at"]) and str(row["completed_at"])[:10] == today_str
        result.append(format_mission_row(row, completed_today))

    return result


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
    return format_mission_row(row, is_completed_today=False)


@router.patch("/{mission_id}/toggle", response_model=Dict[str, Any])
async def toggle_mission(
    mission_id: int,
    target_date: Optional[str] = Query(None, description="Optional YYYY-MM-DD for toggle"),
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Toggle daily completion for today.
    - If not completed today -> mark completed today, log in mission_logs, award XP.
    - If already completed today -> mark uncompleted today, remove today's log.
    Historical logs for other days are never deleted.
    """
    user_id = current_user["id"]
    now_utc = datetime.now(timezone.utc)
    today_str = target_date if target_date else now_utc.strftime("%Y-%m-%d")
    timestamp_str = f"{today_str} {now_utc.strftime('%H:%M:%S')}"

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM missions WHERE id = ? AND user_id = ?", (mission_id, user_id))
    row = cursor.fetchone()

    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail=f"Mission with ID {mission_id} not found")

    cursor.execute(
        "SELECT id FROM mission_logs WHERE user_id = ? AND mission_id = ? AND completed_date = ?",
        (user_id, mission_id, today_str),
    )
    log_row = cursor.fetchone()
    is_completed_today = bool(log_row)

    xp = row["xp_reward"] or 10

    if not is_completed_today:
        cursor.execute(
            """
            INSERT OR REPLACE INTO mission_logs (user_id, mission_id, completed_date, completed_at, xp_reward)
            VALUES (?, ?, ?, ?, ?)
            """,
            (user_id, mission_id, today_str, timestamp_str, xp),
        )
        cursor.execute(
            "UPDATE missions SET completed = 1, completed_at = ? WHERE id = ? AND user_id = ?",
            (timestamp_str, mission_id, user_id),
        )
        new_state = True
    else:
        cursor.execute(
            "DELETE FROM mission_logs WHERE user_id = ? AND mission_id = ? AND completed_date = ?",
            (user_id, mission_id, today_str),
        )
        cursor.execute(
            "SELECT completed_at FROM mission_logs WHERE user_id = ? AND mission_id = ? ORDER BY completed_date DESC LIMIT 1",
            (user_id, mission_id),
        )
        prev_log = cursor.fetchone()
        if prev_log:
            cursor.execute(
                "UPDATE missions SET completed = 0, completed_at = ? WHERE id = ? AND user_id = ?",
                (prev_log["completed_at"], mission_id, user_id),
            )
        else:
            cursor.execute(
                "UPDATE missions SET completed = 0, completed_at = NULL WHERE id = ? AND user_id = ?",
                (mission_id, user_id),
            )
        new_state = False

    conn.commit()
    cursor.execute("SELECT * FROM missions WHERE id = ?", (mission_id,))
    updated_row = cursor.fetchone()
    conn.close()
    return format_mission_row(updated_row, is_completed_today=new_state)

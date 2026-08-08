from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..database import get_connection

router = APIRouter()


class GoalCreateRequest(BaseModel):
    title: str
    description: Optional[str] = ""
    category: Optional[str] = "general"
    target_date: Optional[str] = None


class GoalUpdateRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    status: Optional[str] = None
    target_date: Optional[str] = None


def get_demo_user_id(cursor: Any) -> int:
    cursor.execute("SELECT id FROM users WHERE email = ?", ("demo@masterykeycoach.com",))
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Demo user not found")
    return row["id"]


@router.get("", response_model=List[Dict[str, Any]])
async def list_goals() -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    user_id = get_demo_user_id(cursor)
    cursor.execute("SELECT * FROM goals WHERE user_id = ? ORDER BY id ASC", (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


@router.post("", response_model=Dict[str, Any])
async def create_goal(goal_in: GoalCreateRequest) -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor()
    user_id = get_demo_user_id(cursor)

    cursor.execute(
        """
        INSERT INTO goals (user_id, title, description, category, status, target_date)
        VALUES (?, ?, ?, ?, 'active', ?)
        """,
        (
            user_id,
            goal_in.title,
            goal_in.description,
            goal_in.category or "general",
            goal_in.target_date,
        ),
    )
    conn.commit()
    goal_id = cursor.lastrowid

    cursor.execute("SELECT * FROM goals WHERE id = ?", (goal_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row)


@router.get("/{goal_id}", response_model=Dict[str, Any])
async def get_goal(goal_id: int) -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM goals WHERE id = ?", (goal_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail=f"Goal with ID {goal_id} not found")

    return dict(row)


@router.patch("/{goal_id}", response_model=Dict[str, Any])
async def update_goal(goal_id: int, goal_in: GoalUpdateRequest) -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM goals WHERE id = ?", (goal_id,))
    row = cursor.fetchone()

    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail=f"Goal with ID {goal_id} not found")

    existing_data = dict(row)
    updated_title = goal_in.title if goal_in.title is not None else existing_data["title"]
    updated_desc = goal_in.description if goal_in.description is not None else existing_data["description"]
    updated_cat = goal_in.category if goal_in.category is not None else existing_data["category"]
    updated_status = goal_in.status if goal_in.status is not None else existing_data["status"]
    updated_date = goal_in.target_date if goal_in.target_date is not None else existing_data["target_date"]

    cursor.execute(
        """
        UPDATE goals
        SET title = ?, description = ?, category = ?, status = ?, target_date = ?
        WHERE id = ?
        """,
        (updated_title, updated_desc, updated_cat, updated_status, updated_date, goal_id),
    )
    conn.commit()

    cursor.execute("SELECT * FROM goals WHERE id = ?", (goal_id,))
    updated_row = cursor.fetchone()
    conn.close()
    return dict(updated_row)


@router.delete("/{goal_id}")
async def delete_goal(goal_id: int) -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM goals WHERE id = ?", (goal_id,))
    row = cursor.fetchone()

    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail=f"Goal with ID {goal_id} not found")

    # Decouple missions from goal before deletion
    cursor.execute("UPDATE missions SET goal_id = NULL WHERE goal_id = ?", (goal_id,))
    cursor.execute("DELETE FROM goals WHERE id = ?", (goal_id,))
    conn.commit()
    conn.close()

    return {"message": f"Goal {goal_id} deleted successfully"}

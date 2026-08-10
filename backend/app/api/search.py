from typing import Any, Dict, List
from fastapi import APIRouter, Query

from ..database import get_connection
from ..services.habits import get_demo_user_id

router = APIRouter()


@router.get("", response_model=Dict[str, Any])
async def search_application(q: str = Query(default="", min_length=1)) -> Dict[str, Any]:
    query_str = q.strip()
    if not query_str:
        return {"habits": [], "goals": [], "missions": [], "milestones": [], "journal": [], "count": 0}

    user_id = get_demo_user_id()
    pattern = f"%{query_str}%"

    conn = get_connection()
    cursor = conn.cursor()

    # 1. Search Habits
    cursor.execute(
        """
        SELECT id, title, description, category, status
        FROM habits
        WHERE user_id = ? AND (title LIKE ? OR description LIKE ?)
        LIMIT 10
        """,
        (user_id, pattern, pattern),
    )
    habits = [dict(r) for r in cursor.fetchall()]

    # 2. Search Goals
    cursor.execute(
        """
        SELECT id, title, description, category, status
        FROM goals
        WHERE user_id = ? AND (title LIKE ? OR description LIKE ?)
        LIMIT 10
        """,
        (user_id, pattern, pattern),
    )
    goals = [dict(r) for r in cursor.fetchall()]

    # 3. Search Missions
    cursor.execute(
        """
        SELECT id, title, description, category, completed
        FROM missions
        WHERE (user_id = ? OR user_id IS NULL) AND (title LIKE ? OR description LIKE ?)
        LIMIT 10
        """,
        (user_id, pattern, pattern),
    )
    missions = [dict(r) for r in cursor.fetchall()]

    # 4. Search Blueprint Milestones
    cursor.execute(
        """
        SELECT id, title, description, completed, target_date
        FROM blueprint_milestones
        WHERE blueprint_id IN (SELECT id FROM life_blueprints WHERE user_id = ?)
          AND (title LIKE ? OR description LIKE ?)
        LIMIT 10
        """,
        (user_id, pattern, pattern),
    )
    milestones = [dict(r) for r in cursor.fetchall()]

    # 5. Search Journal Entries
    cursor.execute(
        """
        SELECT id, entry_date, mood, wins_text, challenges_text
        FROM journal_entries
        WHERE user_id = ? AND (wins_text LIKE ? OR challenges_text LIKE ? OR learnings_text LIKE ?)
        LIMIT 10
        """,
        (user_id, pattern, pattern, pattern),
    )
    journal = [dict(r) for r in cursor.fetchall()]

    conn.close()

    total_count = len(habits) + len(goals) + len(missions) + len(milestones) + len(journal)

    return {
        "habits": habits,
        "goals": goals,
        "missions": missions,
        "milestones": milestones,
        "journal": journal,
        "count": total_count,
    }

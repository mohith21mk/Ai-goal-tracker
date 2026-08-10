import datetime
from typing import Any, Dict
from fastapi import APIRouter, Depends

from ..database import get_connection
from ..services.blueprints import get_blueprint_telemetry
from ..services.habits import get_aggregate_habit_stats
from ..services.journal import compute_journal_stats
from .auth import get_current_user

router = APIRouter()


async def compute_telemetry(user_id: int) -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Missions Telemetry
    cursor.execute("SELECT COUNT(*) FROM missions WHERE user_id = ?", (user_id,))
    total_missions = cursor.fetchone()[0] or 0

    cursor.execute("SELECT COUNT(*) FROM missions WHERE user_id = ? AND completed = 1", (user_id,))
    completed_missions = cursor.fetchone()[0] or 0

    mission_percentage = round((completed_missions / total_missions) * 100) if total_missions > 0 else 0
    discipline_score = mission_percentage

    # 2. Mindset Strength
    cursor.execute("SELECT COUNT(*) FROM missions WHERE user_id = ? AND category = 'mindset'", (user_id,))
    total_mindset = cursor.fetchone()[0] or 0

    cursor.execute("SELECT COUNT(*) FROM missions WHERE user_id = ? AND category = 'mindset' AND completed = 1", (user_id,))
    completed_mindset = cursor.fetchone()[0] or 0

    mindset_base = round((completed_mindset / total_mindset) * 100) if total_mindset > 0 else 0

    journal_stats = compute_journal_stats(user_id)
    journal_streak = journal_stats.get("reflection_streak", 0)

    if journal_stats.get("total_entries", 0) > 0:
        journal_bonus = (
            min(journal_streak * 5, 15)
            + round(journal_stats.get("avg_energy_7d", 7) * 0.5)
        )
        mindset_strength = min(mindset_base + journal_bonus, 100)
    else:
        mindset_strength = mindset_base

    # 3. XP Earned
    cursor.execute("SELECT SUM(xp_reward) FROM missions WHERE user_id = ? AND completed = 1", (user_id,))
    xp_row = cursor.fetchone()[0]
    xp_earned = int(xp_row) if xp_row is not None else 0

    # 4. Streak Days
    cursor.execute(
        """
        SELECT DISTINCT DATE(completed_at) as comp_date
        FROM missions
        WHERE user_id = ? AND completed = 1 AND completed_at IS NOT NULL
        ORDER BY comp_date DESC
        """,
        (user_id,),
    )
    date_rows = cursor.fetchall()
    dates = [r["comp_date"] for r in date_rows if r["comp_date"]]

    streak_days = 0
    if dates:
        today = datetime.date.today()
        latest_date = datetime.datetime.strptime(dates[0], "%Y-%m-%d").date()
        if (today - latest_date).days <= 1:
            streak_days = 1
            current = latest_date
            for d_str in dates[1:]:
                d = datetime.datetime.strptime(d_str, "%Y-%m-%d").date()
                if (current - d).days == 1:
                    streak_days += 1
                    current = d
                else:
                    break

    # 5. Habit Telemetry
    habit_stats = get_aggregate_habit_stats(user_id)
    habit_weekly_pct = habit_stats.get("overall_7day_completion_pct", 0)

    streak_component = min(streak_days * 10, 100)
    if habit_stats.get("total_active_habits", 0) > 0:
        consistency = round((mission_percentage * 0.5) + (streak_component * 0.3) + (habit_weekly_pct * 0.2))
    else:
        consistency = round((mission_percentage * 0.5) + (streak_component * 0.5))

    # 6. Goals Telemetry
    cursor.execute("SELECT COUNT(*) FROM goals WHERE user_id = ?", (user_id,))
    total_goals = cursor.fetchone()[0] or 0

    cursor.execute("SELECT COUNT(*) FROM goals WHERE user_id = ? AND status = 'active'", (user_id,))
    active_goals = cursor.fetchone()[0] or 0

    cursor.execute("SELECT COUNT(*) FROM goals WHERE user_id = ? AND status = 'completed'", (user_id,))
    completed_goals = cursor.fetchone()[0] or 0

    goal_completion_comp = round((completed_goals / total_goals) * 100) if total_goals > 0 else 0
    growth_index = round((mission_percentage * 0.6) + (goal_completion_comp * 0.4))

    # 7. Life Blueprint Telemetry
    blueprint_telemetry = get_blueprint_telemetry(user_id)

    conn.close()

    return {
        "discipline_score": discipline_score,
        "mindset_strength": mindset_strength,
        "consistency": consistency,
        "growth_index": growth_index,
        "streak_days": streak_days,
        "xp_earned": xp_earned,
        "mission_completion": {
            "completed": completed_missions,
            "total": total_missions,
            "percentage": mission_percentage,
        },
        "goals": {
            "total": total_goals,
            "active": active_goals,
            "completed": completed_goals,
        },
        "habits": habit_stats,
        "journal": {
            "total_entries": journal_stats.get("total_entries", 0),
            "journal_streak": journal_stats.get("reflection_streak", 0),
            "avg_energy_7d": journal_stats.get("avg_energy_7d", 0.0),
            "latest_mood": journal_stats.get("latest_mood", None),
        },
        "blueprint": blueprint_telemetry,
    }


@router.get("", response_model=Dict[str, Any])
async def get_progress(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    user_id = current_user["id"]
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM missions WHERE user_id = ?", (user_id,))
    total = cursor.fetchone()[0] or 0

    cursor.execute("SELECT COUNT(*) FROM missions WHERE user_id = ? AND completed = 1", (user_id,))
    completed = cursor.fetchone()[0] or 0

    conn.close()

    percentage = round((completed / total) * 100) if total > 0 else 0

    return {
        "completed": completed,
        "total": total,
        "percentage": percentage,
    }


@router.get("/telemetry", response_model=Dict[str, Any])
async def get_telemetry_subroute(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    return await compute_telemetry(current_user["id"])

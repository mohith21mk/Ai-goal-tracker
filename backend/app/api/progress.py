import datetime
from typing import Any, Dict

from fastapi import APIRouter

from ..database import get_connection
from ..services.habits import get_aggregate_habit_stats, get_demo_user_id

router = APIRouter()


async def compute_telemetry() -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Missions Telemetry
    cursor.execute("SELECT COUNT(*) FROM missions")
    total_missions = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM missions WHERE completed = 1")
    completed_missions = cursor.fetchone()[0]

    mission_percentage = round((completed_missions / total_missions) * 100) if total_missions > 0 else 0

    # Discipline Score = overall completion rate (0-100)
    discipline_score = mission_percentage

    # 2. Mindset Strength = mindset completed / mindset total * 100
    cursor.execute("SELECT COUNT(*) FROM missions WHERE category = 'mindset'")
    total_mindset = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM missions WHERE category = 'mindset' AND completed = 1")
    completed_mindset = cursor.fetchone()[0]

    mindset_strength = round((completed_mindset / total_mindset) * 100) if total_mindset > 0 else 0

    # 3. XP Earned = SUM(xp_reward) for completed missions
    cursor.execute("SELECT SUM(xp_reward) FROM missions WHERE completed = 1")
    xp_row = cursor.fetchone()[0]
    xp_earned = int(xp_row) if xp_row is not None else 0

    # 4. Streak Days = consecutive calendar days with completions
    cursor.execute(
        """
        SELECT DISTINCT DATE(completed_at) as comp_date
        FROM missions
        WHERE completed = 1 AND completed_at IS NOT NULL
        ORDER BY comp_date DESC
        """
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

    # 5. Habit Telemetry & Consistency Score Combination
    demo_user_id = get_demo_user_id()
    habit_stats = get_aggregate_habit_stats(demo_user_id)
    habit_weekly_pct = habit_stats.get("overall_7day_completion_pct", 0)

    streak_component = min(streak_days * 10, 100)
    if habit_stats.get("total_active_habits", 0) > 0:
        consistency = round((mission_percentage * 0.5) + (streak_component * 0.3) + (habit_weekly_pct * 0.2))
    else:
        consistency = round((mission_percentage * 0.5) + (streak_component * 0.5))

    # 6. Goals Telemetry
    cursor.execute("SELECT COUNT(*) FROM goals")
    total_goals = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM goals WHERE status = 'active'")
    active_goals = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM goals WHERE status = 'completed'")
    completed_goals = cursor.fetchone()[0]

    goal_completion_comp = round((completed_goals / total_goals) * 100) if total_goals > 0 else 0

    # 7. Growth Index = 60% mission completion + 40% goal completion
    growth_index = round((mission_percentage * 0.6) + (goal_completion_comp * 0.4))

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
    }


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


@router.get("/telemetry", response_model=Dict[str, Any])
async def get_telemetry_subroute() -> Dict[str, Any]:
    return await compute_telemetry()

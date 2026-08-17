import datetime
import hashlib
from typing import Dict, Any, List

from ..database import get_connection
from .blueprints import get_blueprint_telemetry
from .habits import get_aggregate_habit_stats
from .journal import compute_journal_stats


def generate_daily_reflection(user_id: int) -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Gather Missions Data
    cursor.execute("SELECT COUNT(*) FROM missions WHERE user_id = ?", (user_id,))
    total_missions = cursor.fetchone()[0] or 0

    cursor.execute("SELECT COUNT(*) FROM missions WHERE user_id = ? AND completed = 1", (user_id,))
    completed_missions = cursor.fetchone()[0] or 0

    pending_missions = max(0, total_missions - completed_missions)
    mission_pct = round((completed_missions / total_missions) * 100) if total_missions > 0 else 0

    # 2. XP Earned
    cursor.execute("SELECT SUM(xp_reward) FROM missions WHERE user_id = ? AND completed = 1", (user_id,))
    xp_row = cursor.fetchone()[0]
    xp_earned = int(xp_row) if xp_row is not None else 0

    # 3. Mission Streak
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
    dates = [str(r["comp_date"])[:10] for r in date_rows if r["comp_date"]]

    streak_days = 0
    if dates:
        today = datetime.datetime.now(datetime.timezone.utc).date()
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

    # 4. Habits Data
    habit_stats = get_aggregate_habit_stats(user_id)
    completed_habits_today = habit_stats.get("today_completed_count", 0)
    current_habit_streak = habit_stats.get("longest_active_streak", 0)

    # 5. Blueprint Data
    blueprint_telemetry = get_blueprint_telemetry(user_id)
    active_blueprint = blueprint_telemetry.get("active_blueprint")
    blueprint_phase = "Phase 1: Foundation"
    blueprint_progress = 0

    if active_blueprint and active_blueprint.get("phases"):
        phases = active_blueprint["phases"]
        active_phase_obj = next((p for p in phases if p.get("status") == "in_progress"), phases[0])
        blueprint_phase = active_phase_obj.get("title", "Phase 1: Foundation Setup")
        blueprint_progress = active_phase_obj.get("progress_pct", 0)

    # 6. Goals Progress
    cursor.execute("SELECT title, category, status FROM goals WHERE user_id = ? AND status = 'active' ORDER BY id ASC LIMIT 1", (user_id,))
    active_goal_row = cursor.fetchone()
    active_goal_title = active_goal_row["title"] if active_goal_row else "AI Engineering Mastery"

    conn.close()

    today_date_str = datetime.datetime.now(datetime.timezone.utc).strftime("%B %d, %Y")

    # 7. Generate Data-Driven Deterministic Reflection Messages
    reflections: List[Dict[str, Any]] = []

    if completed_missions > 0:
        reflections.append({
            "text": f"You completed {completed_missions} of {total_missions} missions today and earned {xp_earned} XP. Your consistency is building unstoppable momentum.",
            "category": "missions",
            "highlight_metric": f"{completed_missions}/{total_missions} Missions",
            "highlight_color": "#38BDF8"
        })

    if streak_days > 0:
        reflections.append({
            "text": f"{streak_days}-day discipline streak active. You don't break promises to yourself. Small choices today create an extraordinary future.",
            "category": "streak",
            "highlight_metric": f"{streak_days} Day Streak",
            "highlight_color": "#FBBF24"
        })

    if blueprint_progress > 0 or active_blueprint:
        reflections.append({
            "text": f"{blueprint_phase} is {blueprint_progress}% complete. You are actively stepping into the high-performance identity you are training to be.",
            "category": "blueprint",
            "highlight_metric": f"{blueprint_progress}% Blueprint",
            "highlight_color": "#A78BFA"
        })

    if completed_habits_today > 0 or current_habit_streak > 0:
        reflections.append({
            "text": f"Completed {completed_habits_today} habit protocols today. Small daily actions compound into extraordinary long-term freedom.",
            "category": "habits",
            "highlight_metric": f"{completed_habits_today} Habits Done",
            "highlight_color": "#10B981"
        })

    # Default fallback reflections if early state
    reflections.append({
        "text": f"Focused execution on '{active_goal_title}'. You are not just dreaming—you are building your legacy step by step.",
        "category": "goals",
        "highlight_metric": active_goal_title,
        "highlight_color": "#3B82F6"
    })
    reflections.append({
        "text": "Discipline is choosing between what you want now and what you want most. Execute your next mission with absolute focus.",
        "category": "mindset",
        "highlight_metric": "Daily Protocol",
        "highlight_color": "#A78BFA"
    })

    # Pick reflection based on day-of-year + user metrics hash so it stays stable throughout the day
    date_hash_val = int(hashlib.md5(today_date_str.encode("utf-8")).hexdigest(), 16)
    selected_idx = date_hash_val % len(reflections)
    selected_reflection = reflections[selected_idx]

    return {
        "reflection": selected_reflection["text"],
        "date": today_date_str,
        "category": selected_reflection["category"],
        "highlight_metric": selected_reflection["highlight_metric"],
        "highlight_color": selected_reflection["highlight_color"],
        "metrics": {
            "completed_missions": completed_missions,
            "total_missions": total_missions,
            "pending_missions": pending_missions,
            "xp_earned": xp_earned,
            "streak_days": streak_days,
            "completed_habits_today": completed_habits_today,
            "current_habit_streak": current_habit_streak,
            "blueprint_phase": blueprint_phase,
            "blueprint_progress": blueprint_progress,
            "active_goal_title": active_goal_title,
        }
    }

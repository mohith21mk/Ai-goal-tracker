import datetime
from typing import Any, Dict, List
from fastapi import APIRouter, Depends

from ..database import get_connection
from ..services.blueprints import get_blueprint_telemetry
from ..services.habits import get_aggregate_habit_stats
from ..services.journal import compute_journal_stats
from ..services.progression import calculate_user_xp, get_user_progression
from .auth import get_current_user

router = APIRouter()


def _compute_daily_snapshot(cursor: Any, user_id: int, date_cutoff: str) -> Dict[str, Any]:
    """Helper to compute historical telemetry snapshot for a specific date cutoff (YYYY-MM-DD 23:59:59)."""
    cutoff_date = date_cutoff[:10]

    # 1. Missions created on or before cutoff
    cursor.execute(
        "SELECT COUNT(*) FROM missions WHERE user_id = ? AND (created_at <= ? OR created_at IS NULL)",
        (user_id, date_cutoff),
    )
    tot_m = cursor.fetchone()[0] or 0

    # Missions completed on or before cutoff
    cursor.execute(
        "SELECT COUNT(*), COALESCE(SUM(xp_reward), 0) FROM missions WHERE user_id = ? AND completed = 1 AND (completed_at <= ? OR (completed_at IS NULL AND (created_at <= ? OR created_at IS NULL)))",
        (user_id, date_cutoff, date_cutoff),
    )
    m_comp_row = cursor.fetchone()
    comp_m = m_comp_row[0] or 0
    xp_m = int(m_comp_row[1] or 0)
    m_pct = round((comp_m / tot_m) * 100) if tot_m > 0 else 0

    # 2. Mindset missions created & completed on or before cutoff
    cursor.execute(
        "SELECT COUNT(*) FROM missions WHERE user_id = ? AND category = 'mindset' AND (created_at <= ? OR created_at IS NULL)",
        (user_id, date_cutoff),
    )
    tot_mind = cursor.fetchone()[0] or 0

    cursor.execute(
        "SELECT COUNT(*) FROM missions WHERE user_id = ? AND category = 'mindset' AND completed = 1 AND (completed_at <= ? OR (completed_at IS NULL AND (created_at <= ? OR created_at IS NULL)))",
        (user_id, date_cutoff, date_cutoff),
    )
    comp_mind = cursor.fetchone()[0] or 0
    if tot_mind > 0:
        mind_base = round((comp_mind / tot_mind) * 100)
    else:
        # Fallback to general mission completion percentage if no specific mindset category missions
        mind_base = m_pct

    # Journal reflections logged on or before cutoff date
    cursor.execute(
        "SELECT COUNT(*), AVG(energy_level) FROM journal_entries WHERE user_id = ? AND entry_date <= ?",
        (user_id, cutoff_date),
    )
    j_row = cursor.fetchone()
    tot_j = j_row[0] or 0
    avg_energy_j = float(j_row[1] or 0.0)

    # Journal streak up to cutoff_date
    cursor.execute(
        "SELECT DISTINCT entry_date FROM journal_entries WHERE user_id = ? AND entry_date <= ? ORDER BY entry_date DESC",
        (user_id, cutoff_date),
    )
    j_dates = [r[0] for r in cursor.fetchall() if r[0]]
    j_streak = 0
    if j_dates:
        try:
            curr_dt = datetime.datetime.strptime(cutoff_date, "%Y-%m-%d").date()
            latest_j_dt = datetime.datetime.strptime(j_dates[0], "%Y-%m-%d").date()
            if (curr_dt - latest_j_dt).days <= 1:
                j_streak = 1
                ref_dt = latest_j_dt
                for d_str in j_dates[1:]:
                    d = datetime.datetime.strptime(d_str, "%Y-%m-%d").date()
                    if (ref_dt - d).days == 1:
                        j_streak += 1
                        ref_dt = d
                    else:
                        break
        except Exception:
            j_streak = len(j_dates)

    if tot_j > 0:
        j_streak_score = min(j_streak * 20, 100)
        energy_score = min(round(avg_energy_j * 10), 100)
        mind = round((mind_base * 0.40) + (j_streak_score * 0.30) + (energy_score * 0.30))
    else:
        mind = mind_base

    # 3. Habits active & logged on or before cutoff
    cursor.execute(
        "SELECT COUNT(*) FROM habits WHERE user_id = ? AND (created_at <= ? OR created_at IS NULL)",
        (user_id, date_cutoff),
    )
    tot_habits = cursor.fetchone()[0] or 0

    try:
        c_dt = datetime.datetime.strptime(cutoff_date, "%Y-%m-%d").date()
        start_7d = (c_dt - datetime.timedelta(days=6)).strftime("%Y-%m-%d")
    except ValueError:
        start_7d = cutoff_date

    cursor.execute(
        "SELECT COUNT(*) FROM habit_logs WHERE user_id = ? AND completed_date BETWEEN ? AND ?",
        (user_id, start_7d, cutoff_date),
    )
    completed_7d_habits = cursor.fetchone()[0] or 0
    possible_7d_habits = max(1, tot_habits * 7)
    h_weekly_pct = round((completed_7d_habits / possible_7d_habits) * 100) if tot_habits > 0 else 0

    cursor.execute(
        "SELECT COUNT(*) FROM habit_logs WHERE user_id = ? AND completed_date <= ?",
        (user_id, cutoff_date),
    )
    tot_h_logs = cursor.fetchone()[0] or 0
    total_xp_cutoff = xp_m + (tot_h_logs * 15)

    # 4. Streak Days up to cutoff
    cursor.execute(
        "SELECT DISTINCT COALESCE(completed_at, created_at, CURRENT_TIMESTAMP) FROM missions WHERE user_id = ? AND completed = 1 AND (completed_at <= ? OR (completed_at IS NULL AND (created_at <= ? OR created_at IS NULL)))",
        (user_id, date_cutoff, date_cutoff),
    )
    m_dates = [str(r[0])[:10] for r in cursor.fetchall() if r[0]]

    cursor.execute(
        "SELECT DISTINCT completed_date FROM habit_logs WHERE user_id = ? AND completed_date <= ?",
        (user_id, cutoff_date),
    )
    h_dates = [str(r[0])[:10] for r in cursor.fetchall() if r[0]]

    active_dates = sorted(set(m_dates + h_dates), reverse=True)
    streak = 0
    if active_dates:
        try:
            c_dt = datetime.datetime.strptime(cutoff_date, "%Y-%m-%d").date()
            latest_act_dt = datetime.datetime.strptime(active_dates[0], "%Y-%m-%d").date()
            if (c_dt - latest_act_dt).days <= 1:
                streak = 1
                ref_dt = latest_act_dt
                for d_str in active_dates[1:]:
                    d = datetime.datetime.strptime(d_str, "%Y-%m-%d").date()
                    if (ref_dt - d).days == 1:
                        streak += 1
                        ref_dt = d
                    else:
                        break
        except Exception:
            streak = len(active_dates)

    streak_comp = min(streak * 10, 100)

    # Discipline & Consistency
    if tot_m > 0 or tot_habits > 0 or tot_h_logs > 0:
        disc = round((m_pct * 0.50) + (h_weekly_pct * 0.30) + (streak_comp * 0.20))
        cons = round((h_weekly_pct * 0.40) + (m_pct * 0.40) + (streak_comp * 0.20))
    else:
        disc = 0
        cons = 0

    # 5. Goals & Financial Goals on or before cutoff
    cursor.execute(
        "SELECT COUNT(*), SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) FROM goals WHERE user_id = ? AND (created_at <= ? OR created_at IS NULL)",
        (user_id, date_cutoff),
    )
    g_row = cursor.fetchone()
    tot_g = g_row[0] or 0
    comp_g = g_row[1] or 0
    g_pct = round((comp_g / tot_g) * 100) if tot_g > 0 else 0

    cursor.execute(
        """
        SELECT COUNT(*), SUM(CASE WHEN m.completed = 1 THEN 1 ELSE 0 END)
        FROM blueprint_milestones m
        JOIN life_blueprints b ON m.blueprint_id = b.id
        WHERE b.user_id = ? AND (m.created_at <= ? OR m.created_at IS NULL)
        """,
        (user_id, date_cutoff),
    )
    bp_row = cursor.fetchone()
    tot_bp = bp_row[0] or 0
    comp_bp = bp_row[1] or 0
    bp_pct = round((comp_bp / tot_bp) * 100) if tot_bp > 0 else 0

    if tot_g > 0 or bp_pct > 0 or tot_m > 0:
        grow = round((g_pct * 0.40) + (bp_pct * 0.30) + (m_pct * 0.30))
    else:
        grow = 0

    cursor.execute(
        """
        SELECT COUNT(*), SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END)
        FROM goals
        WHERE user_id = ? AND (created_at <= ? OR created_at IS NULL) AND (
            LOWER(category) IN ('finance', 'wealth', 'financial', 'money') OR
            LOWER(title) LIKE '%finance%' OR LOWER(title) LIKE '%wealth%' OR
            LOWER(title) LIKE '%money%' OR LOWER(title) LIKE '%freedom%' OR LOWER(title) LIKE '%fund%'
        )
        """,
        (user_id, date_cutoff),
    )
    fin_row = cursor.fetchone()
    tot_fin = fin_row[0] or 0
    comp_fin = fin_row[1] or 0
    fin_pct = round((comp_fin / tot_fin) * 100) if tot_fin > 0 else 0

    return {
        "discipline_score": disc,
        "mindset_strength": mind,
        "consistency": cons,
        "growth_index": grow,
        "financial_goal": fin_pct,
        "completed_missions": comp_m,
        "streak_days": streak,
        "xp_earned": total_xp_cutoff,
    }


def compute_telemetry_sync(user_id: int) -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor()

    today_dt = datetime.datetime.now(datetime.timezone.utc).date()
    now_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    # Current Live Snapshot
    current_snap = _compute_daily_snapshot(cursor, user_id, now_str)

    # 1. Missions Telemetry
    cursor.execute("SELECT COUNT(*) FROM missions WHERE user_id = ?", (user_id,))
    total_missions = cursor.fetchone()[0] or 0
    cursor.execute("SELECT COUNT(*) FROM missions WHERE user_id = ? AND completed = 1", (user_id,))
    completed_missions = cursor.fetchone()[0] or 0
    mission_percentage = round((completed_missions / total_missions) * 100) if total_missions > 0 else 0

    # 2. Goals Telemetry
    cursor.execute("SELECT COUNT(*) FROM goals WHERE user_id = ?", (user_id,))
    total_goals = cursor.fetchone()[0] or 0
    cursor.execute("SELECT COUNT(*) FROM goals WHERE user_id = ? AND status = 'active'", (user_id,))
    active_goals = cursor.fetchone()[0] or 0
    cursor.execute("SELECT COUNT(*) FROM goals WHERE user_id = ? AND status = 'completed'", (user_id,))
    completed_goals = cursor.fetchone()[0] or 0

    # 3. Habits Telemetry
    habit_stats = get_aggregate_habit_stats(user_id)

    # 4. Journal & Blueprint Telemetry
    journal_stats = compute_journal_stats(user_id)
    blueprint_telemetry = get_blueprint_telemetry(user_id)

    # 5. Authoritative Progression (XP, Level, Rank)
    progression = get_user_progression(user_id)

    # 5. Compute Historical 7-Day Sparkline Arrays
    sparklines = {
        "discipline_score": [],
        "mindset_strength": [],
        "consistency": [],
        "growth_index": [],
        "financial_goal": [],
        "missions_completed": [],
        "streak_days": [],
        "xp_earned": [],
    }

    for i in range(6, -1, -1):
        target_day = today_dt - datetime.timedelta(days=i)
        cutoff_str = f"{target_day.strftime('%Y-%m-%d')} 23:59:59"
        snap = _compute_daily_snapshot(cursor, user_id, cutoff_str)
        sparklines["discipline_score"].append(snap["discipline_score"])
        sparklines["mindset_strength"].append(snap["mindset_strength"])
        sparklines["consistency"].append(snap["consistency"])
        sparklines["growth_index"].append(snap["growth_index"])
        sparklines["financial_goal"].append(snap["financial_goal"])
        sparklines["missions_completed"].append(snap["completed_missions"])
        sparklines["streak_days"].append(snap["streak_days"])
        sparklines["xp_earned"].append(snap["xp_earned"])

    prev_discipline = sparklines["discipline_score"][5]
    prev_mindset = sparklines["mindset_strength"][5]
    prev_consistency = sparklines["consistency"][5]
    prev_growth = sparklines["growth_index"][5]
    prev_fin = sparklines["financial_goal"][5]
    prev_missions = sparklines["missions_completed"][5]
    prev_streak = sparklines["streak_days"][5]
    prev_xp = sparklines["xp_earned"][5]

    conn.close()

    return {
        "discipline_score": current_snap["discipline_score"],
        "discipline_score_change": current_snap["discipline_score"] - prev_discipline,
        "mindset_strength": current_snap["mindset_strength"],
        "mindset_strength_change": current_snap["mindset_strength"] - prev_mindset,
        "consistency": current_snap["consistency"],
        "consistency_change": current_snap["consistency"] - prev_consistency,
        "growth_index": current_snap["growth_index"],
        "growth_index_change": current_snap["growth_index"] - prev_growth,
        "financial_goal": current_snap["financial_goal"],
        "financial_goal_change": current_snap["financial_goal"] - prev_fin,
        "financial_goal_pct": current_snap["financial_goal"],
        "missions_completed_change": current_snap["completed_missions"] - prev_missions,
        "streak_days": current_snap["streak_days"],
        "streak_days_change": current_snap["streak_days"] - prev_streak,
        "xp_earned": progression["total_xp"],
        "xp_earned_change": progression["total_xp"] - prev_xp,
        "progression": progression,
        "sparklines": sparklines,
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
            "journal_streak": journal_stats.get("journal_streak", 0),
            "avg_energy_7d": journal_stats.get("avg_energy_7d", 0.0),
            "latest_mood": journal_stats.get("latest_mood", None),
        },
        "blueprint": blueprint_telemetry,
    }


async def compute_telemetry(user_id: int) -> Dict[str, Any]:
    try:
        return compute_telemetry_sync(user_id)
    except Exception as e:
        from ..services.logger import logger
        logger.exception(f"Error computing telemetry for user {user_id}: {e}")
        prog = get_user_progression(user_id)
        return {
            "discipline_score": 0,
            "discipline_score_change": 0,
            "mindset_strength": 0,
            "mindset_strength_change": 0,
            "consistency": 0,
            "consistency_change": 0,
            "growth_index": 0,
            "growth_index_change": 0,
            "financial_goal": 0,
            "financial_goal_change": 0,
            "missions_completed_change": 0,
            "streak_days": 0,
            "streak_days_change": 0,
            "xp_earned": prog["total_xp"],
            "xp_earned_change": 0,
            "progression": prog,
            "sparklines": {
                "discipline_score": [0, 0, 0, 0, 0, 0, 0],
                "mindset_strength": [0, 0, 0, 0, 0, 0, 0],
                "consistency": [0, 0, 0, 0, 0, 0, 0],
                "growth_index": [0, 0, 0, 0, 0, 0, 0],
                "financial_goal": [0, 0, 0, 0, 0, 0, 0],
                "missions_completed": [0, 0, 0, 0, 0, 0, 0],
                "streak_days": [0, 0, 0, 0, 0, 0, 0],
                "xp_earned": [0, 0, 0, 0, 0, 0, 0],
            },
            "mission_completion": {"completed": 0, "total": 0, "percentage": 0},
            "goals": {"total": 0, "active": 0, "completed": 0},
            "habits": {"active_habits_count": 0, "habits": []},
            "journal": {"total_entries": 0, "journal_streak": 0, "avg_energy_7d": 0.0, "latest_mood": None},
            "blueprint": {"active_blueprint": None, "completion_percentage": 0},
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

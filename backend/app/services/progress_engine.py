import datetime
from typing import Any, Dict, List, Optional, Set, Tuple

from ..database import get_connection
from ..services.blueprints import get_blueprint_telemetry
from ..services.habits import get_aggregate_habit_stats
from ..services.journal import compute_journal_stats
from ..services.progression import calculate_user_xp, get_user_progression


def _parse_date(val: Any) -> Optional[datetime.date]:
    """Safely parse date string or datetime into a date object."""
    if not val:
        return None
    s = str(val)[:10]
    try:
        return datetime.datetime.strptime(s, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None


def calculate_streak_metrics(active_dates: Set[str], reference_date: datetime.date) -> Tuple[int, int]:
    """
    Calculate (current_streak, longest_streak) up to reference_date.
    A streak continues if active on reference_date or reference_date - 1 day.
    """
    if not active_dates:
        return 0, 0

    parsed_dates = sorted(
        [d for d in (_parse_date(s) for s in active_dates) if d and d <= reference_date]
    )

    if not parsed_dates:
        return 0, 0

    # Calculate longest streak across all history up to reference date
    longest_streak = 1
    running_streak = 1
    for i in range(1, len(parsed_dates)):
        diff = (parsed_dates[i] - parsed_dates[i - 1]).days
        if diff == 1:
            running_streak += 1
            if running_streak > longest_streak:
                longest_streak = running_streak
        elif diff > 1:
            running_streak = 1

    if running_streak > longest_streak:
        longest_streak = running_streak

    # Calculate current streak ending on reference_date or reference_date - 1
    current_streak = 0
    latest_date = parsed_dates[-1]
    days_since_latest = (reference_date - latest_date).days

    if days_since_latest <= 1:
        current_streak = 1
        curr_ref = latest_date
        for prev_date in reversed(parsed_dates[:-1]):
            if (curr_ref - prev_date).days == 1:
                current_streak += 1
                curr_ref = prev_date
            elif (curr_ref - prev_date).days == 0:
                continue
            else:
                break

    return current_streak, longest_streak


def compute_daily_progress_from_records(
    missions: List[Dict[str, Any]],
    habits: List[Dict[str, Any]],
    habit_logs: List[Dict[str, Any]],
    target_date_str: str,
) -> Dict[str, Any]:
    """
    Compute progress strictly for target_date_str (YYYY-MM-DD).
    Zero DB queries.
    """
    # 1. Missions completed on target_date
    completed_missions_today = [
        m for m in missions
        if m.get("completed") == 1 and (
            (m.get("completed_at") and str(m["completed_at"])[:10] == target_date_str) or
            (not m.get("completed_at") and m.get("created_at") and str(m["created_at"])[:10] == target_date_str)
        )
    ]
    missions_completed_count = len(completed_missions_today)
    missions_xp_today = sum(int(m.get("xp_reward") or 0) for m in completed_missions_today)

    # 2. Missions scheduled/active for target_date
    # Active missions: created on or before target date, and either incomplete or completed on target_date
    active_missions_today = [
        m for m in missions
        if (not m.get("created_at") or str(m["created_at"])[:10] <= target_date_str) and (
            m.get("completed") == 0 or
            (m.get("completed_at") and str(m["completed_at"])[:10] == target_date_str) or
            (not m.get("completed_at") and m.get("created_at") and str(m["created_at"])[:10] == target_date_str)
        )
    ]
    total_missions_today = max(len(active_missions_today), missions_completed_count)

    # 3. Habits logged on target_date
    habits_logged_today = [
        l for l in habit_logs
        if l.get("completed_date") and str(l["completed_date"])[:10] == target_date_str
    ]
    habits_completed_count = len(habits_logged_today)
    habits_xp_today = habits_completed_count * 15

    # 4. Total habits scheduled for target_date
    active_habits_today = [
        h for h in habits
        if not h.get("created_at") or str(h["created_at"])[:10] <= target_date_str
    ]
    total_habits_today = max(len(active_habits_today), habits_completed_count)

    completed_actions = missions_completed_count + habits_completed_count
    total_actions = total_missions_today + total_habits_today
    if total_actions < completed_actions:
        total_actions = completed_actions

    completion_percentage = (
        round((completed_actions / total_actions) * 100) if total_actions > 0 else 0
    )
    xp_earned_today = missions_xp_today + habits_xp_today

    return {
        "date": target_date_str,
        "completed_actions": completed_actions,
        "total_actions": total_actions,
        "completion_percentage": min(100, completion_percentage),
        "missions_completed": missions_completed_count,
        "total_missions": total_missions_today,
        "habits_completed": habits_completed_count,
        "total_habits": total_habits_today,
        "xp_earned_today": xp_earned_today,
    }


def compute_overall_performance_from_records(
    missions: List[Dict[str, Any]],
    journal_entries: List[Dict[str, Any]],
    habits: List[Dict[str, Any]],
    habit_logs: List[Dict[str, Any]],
    goals: List[Dict[str, Any]],
    milestones: List[Dict[str, Any]],
    account_created_at: Optional[str],
    date_cutoff_str: str,
) -> Dict[str, Any]:
    """
    Compute normalized, gradual, lifetime overall performance metrics up to date_cutoff_str.
    Zero DB queries.
    """
    cutoff_date = _parse_date(date_cutoff_str) or datetime.date.today()
    cutoff_datetime_str = f"{cutoff_date.strftime('%Y-%m-%d')} 23:59:59"

    # 1. Account Age & Active Days Calculation
    created_date = _parse_date(account_created_at) or cutoff_date
    account_age_days = max(1, (cutoff_date - created_date).days + 1)

    m_active_dates = {
        str(m.get("completed_at") or m.get("created_at"))[:10]
        for m in missions
        if m.get("completed") == 1 and (
            (m.get("completed_at") and str(m["completed_at"]) <= cutoff_datetime_str) or
            (not m.get("completed_at") and (not m.get("created_at") or str(m["created_at"]) <= cutoff_datetime_str))
        )
    }
    h_active_dates = {
        str(l["completed_date"])[:10]
        for l in habit_logs
        if l.get("completed_date") and str(l["completed_date"]) <= str(cutoff_date)
    }
    j_active_dates = {
        str(j["entry_date"])[:10]
        for j in journal_entries
        if j.get("entry_date") and str(j["entry_date"]) <= str(cutoff_date)
    }

    all_active_dates = m_active_dates | h_active_dates | j_active_dates
    active_days_count = len(all_active_dates)

    current_streak, longest_streak = calculate_streak_metrics(all_active_dates, cutoff_date)

    # 2. Historical Missions in Scope
    missions_in_scope = [
        m for m in missions
        if not m.get("created_at") or str(m["created_at"]) <= cutoff_datetime_str
    ]
    total_missions_hist = len(missions_in_scope)
    completed_missions_hist = sum(
        1 for m in missions_in_scope
        if m.get("completed") == 1 and (
            not m.get("completed_at") or str(m["completed_at"]) <= cutoff_datetime_str
        )
    )

    if total_missions_hist > 0:
        raw_mission_rate = (completed_missions_hist / total_missions_hist) * 100.0
        volume_weight = min(1.0, total_missions_hist / 10.0)
        mission_score = (raw_mission_rate * volume_weight) + (50.0 * (1.0 - volume_weight) * (raw_mission_rate / 100.0))
    else:
        mission_score = 0.0

    # 3. Habit Consistency Calculation (28-day rolling window)
    start_28d = (cutoff_date - datetime.timedelta(days=27)).strftime("%Y-%m-%d")
    habits_in_scope = [
        h for h in habits
        if not h.get("created_at") or str(h["created_at"]) <= cutoff_datetime_str
    ]
    tot_habits_count = len(habits_in_scope)

    logs_28d = [
        l for l in habit_logs
        if l.get("completed_date") and start_28d <= str(l["completed_date"])[:10] <= str(cutoff_date)
    ]
    completed_28d_logs = len(logs_28d)

    days_in_window = min(account_age_days, 28)
    expected_logs_28d = max(1, tot_habits_count * days_in_window)
    raw_habit_pct = (completed_28d_logs / expected_logs_28d) * 100.0 if tot_habits_count > 0 else 0.0
    habit_consistency_score = min(100.0, raw_habit_pct)

    active_density_score = min(100.0, (active_days_count / account_age_days) * 100.0)
    streak_score = min(100.0, (current_streak / 30.0) * 100.0)

    # 4. Overall Discipline Score Formula
    if total_missions_hist > 0 or tot_habits_count > 0 or active_days_count > 0:
        raw_discipline = (
            (mission_score * 0.40) +
            (active_density_score * 0.30) +
            (habit_consistency_score * 0.20) +
            (streak_score * 0.10)
        )
        discipline_score = round(min(100.0, max(0.0, raw_discipline)), 1)
    else:
        discipline_score = 0.0

    # 5. Mindset Strength Formula
    mindset_missions = [
        m for m in missions_in_scope
        if (m.get("category") or "").lower() == "mindset"
    ]
    tot_mindset_m = len(mindset_missions)
    comp_mindset_m = sum(
        1 for m in mindset_missions
        if m.get("completed") == 1 and (
            not m.get("completed_at") or str(m["completed_at"]) <= cutoff_datetime_str
        )
    )

    if tot_mindset_m > 0:
        raw_mind_rate = (comp_mindset_m / tot_mindset_m) * 100.0
        mind_vol = min(1.0, tot_mindset_m / 5.0)
        mindset_m_score = (raw_mind_rate * mind_vol) + (50.0 * (1.0 - mind_vol) * (raw_mind_rate / 100.0))
    else:
        mindset_m_score = mission_score

    journals_in_scope = [
        j for j in journal_entries
        if j.get("entry_date") and str(j["entry_date"])[:10] <= str(cutoff_date)
    ]
    tot_journals = len(journals_in_scope)
    avg_energy = (
        sum(float(j.get("energy_level") or 0.0) for j in journals_in_scope) / tot_journals
    ) if tot_journals > 0 else 0.0

    journal_freq_score = min(100.0, (tot_journals / max(1, active_days_count)) * 100.0) if tot_journals > 0 else 0.0
    energy_score = min(100.0, avg_energy * 10.0) if tot_journals > 0 else 50.0

    if tot_journals > 0 or tot_mindset_m > 0 or total_missions_hist > 0:
        if tot_journals > 0:
            raw_mindset = (
                (mindset_m_score * 0.40) +
                (journal_freq_score * 0.35) +
                (energy_score * 0.25)
            )
        else:
            raw_mindset = (mindset_m_score * 0.60) + (active_density_score * 0.40)
        mindset_strength = round(min(100.0, max(0.0, raw_mindset)), 1)
    else:
        mindset_strength = 0.0

    # 6. Consistency Formula
    streak_stability = (
        (current_streak / max(1, longest_streak)) * 100.0
    ) if longest_streak > 0 else 0.0

    if active_days_count > 0 or tot_habits_count > 0 or total_missions_hist > 0:
        raw_consistency = (
            (active_density_score * 0.40) +
            (habit_consistency_score * 0.35) +
            (streak_stability * 0.25)
        )
        consistency = round(min(100.0, max(0.0, raw_consistency)), 1)
    else:
        consistency = 0.0

    # 7. Growth Index Formula
    goals_in_scope = [
        g for g in goals
        if not g.get("created_at") or str(g["created_at"]) <= cutoff_datetime_str
    ]
    tot_goals = len(goals_in_scope)
    comp_goals = sum(1 for g in goals_in_scope if g.get("status") == "completed")
    goal_score = (comp_goals / tot_goals) * 100.0 if tot_goals > 0 else 0.0

    milestones_in_scope = [
        ms for ms in milestones
        if not ms.get("created_at") or str(ms["created_at"]) <= cutoff_datetime_str
    ]
    tot_milestones = len(milestones_in_scope)
    comp_milestones = sum(1 for ms in milestones_in_scope if ms.get("completed") == 1)
    milestone_score = (comp_milestones / tot_milestones) * 100.0 if tot_milestones > 0 else 0.0

    mission_xp_hist = sum(
        int(m.get("xp_reward") or 0)
        for m in missions_in_scope
        if m.get("completed") == 1 and (
            not m.get("completed_at") or str(m["completed_at"]) <= cutoff_datetime_str
        )
    )
    habit_xp_hist = sum(
        15 for l in habit_logs
        if l.get("completed_date") and str(l["completed_date"])[:10] <= str(cutoff_date)
    )
    total_xp_hist = mission_xp_hist + habit_xp_hist
    xp_level = (total_xp_hist // 500) + 1
    xp_velocity_score = min(100.0, (total_xp_hist / 5000.0) * 100.0)

    if tot_goals > 0 or tot_milestones > 0 or total_missions_hist > 0 or total_xp_hist > 0:
        if tot_goals > 0 or tot_milestones > 0:
            raw_growth = (
                (goal_score * 0.35) +
                (milestone_score * 0.35) +
                (xp_velocity_score * 0.30)
            )
        else:
            raw_growth = (mission_score * 0.50) + (xp_velocity_score * 0.50)
        growth_index = round(min(100.0, max(0.0, raw_growth)), 1)
    else:
        growth_index = 0.0

    # 8. Financial Goal Progress
    fin_goals = [
        g for g in goals_in_scope
        if (g.get("category") or "").lower() in ("finance", "wealth", "financial", "money") or
        any(k in (g.get("title") or "").lower() for k in ("finance", "wealth", "money", "freedom", "fund"))
    ]
    tot_fin = len(fin_goals)
    comp_fin = sum(1 for g in fin_goals if g.get("status") == "completed")
    fin_pct = round((comp_fin / tot_fin) * 100) if tot_fin > 0 else 0

    return {
        "discipline_score": discipline_score,
        "mindset_strength": mindset_strength,
        "consistency": consistency,
        "growth_index": growth_index,
        "financial_goal": fin_pct,
        "active_days": active_days_count,
        "current_streak": current_streak,
        "longest_streak": longest_streak,
        "streak_days": current_streak,
        "completed_missions": completed_missions_hist,
        "total_missions": total_missions_hist,
        "total_goals": tot_goals,
        "completed_goals": comp_goals,
        "total_habits": tot_habits_count,
        "total_journal_entries": tot_journals,
        "total_xp": total_xp_hist,
        "level": xp_level,
    }


def compute_comprehensive_progress(user_id: int) -> Dict[str, Any]:
    """
    Unified, high-efficiency calculation returning separated overall performance and daily progress.
    Fetches raw user data in 7 fast batch queries.
    """
    conn = get_connection()
    cursor = conn.cursor()

    today_dt = datetime.datetime.now(datetime.timezone.utc).date()
    today_str = today_dt.strftime("%Y-%m-%d")
    now_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("SELECT created_at FROM users WHERE id = ?", (user_id,))
    user_row = cursor.fetchone()
    account_created_at = user_row["created_at"] if user_row else None

    cursor.execute(
        "SELECT id, category, xp_reward, completed, created_at, completed_at FROM missions WHERE user_id = ?",
        (user_id,),
    )
    missions = [dict(r) for r in cursor.fetchall()]

    cursor.execute(
        "SELECT id, entry_date, energy_level FROM journal_entries WHERE user_id = ?",
        (user_id,),
    )
    journal_entries = [dict(r) for r in cursor.fetchall()]

    cursor.execute(
        "SELECT id, created_at FROM habits WHERE user_id = ?",
        (user_id,),
    )
    habits = [dict(r) for r in cursor.fetchall()]

    cursor.execute(
        "SELECT id, habit_id, completed_date FROM habit_logs WHERE user_id = ?",
        (user_id,),
    )
    habit_logs = [dict(r) for r in cursor.fetchall()]

    cursor.execute(
        "SELECT id, title, category, status, created_at FROM goals WHERE user_id = ?",
        (user_id,),
    )
    goals = [dict(r) for r in cursor.fetchall()]

    cursor.execute(
        """
        SELECT m.id, m.completed, m.created_at 
        FROM blueprint_milestones m 
        JOIN life_blueprints b ON m.blueprint_id = b.id 
        WHERE b.user_id = ?
        """,
        (user_id,),
    )
    milestones = [dict(r) for r in cursor.fetchall()]

    conn.close()

    # 1. Compute System 2 — Daily Progress (Today Only)
    daily_progress = compute_daily_progress_from_records(missions, habits, habit_logs, today_str)

    # 2. Compute System 1 — Overall Performance Metrics (Lifetime)
    current_overall = compute_overall_performance_from_records(
        missions, journal_entries, habits, habit_logs, goals, milestones, account_created_at, now_str
    )

    progression = get_user_progression(user_id)
    habit_stats = get_aggregate_habit_stats(user_id)
    journal_stats = compute_journal_stats(user_id)
    blueprint_telemetry = get_blueprint_telemetry(user_id)

    # 3. Compute Historical 7-Day Sparkline Arrays in memory
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
        snap = compute_overall_performance_from_records(
            missions, journal_entries, habits, habit_logs, goals, milestones, account_created_at, cutoff_str
        )
        sparklines["discipline_score"].append(snap["discipline_score"])
        sparklines["mindset_strength"].append(snap["mindset_strength"])
        sparklines["consistency"].append(snap["consistency"])
        sparklines["growth_index"].append(snap["growth_index"])
        sparklines["financial_goal"].append(snap["financial_goal"])
        sparklines["missions_completed"].append(snap["completed_missions"])
        sparklines["streak_days"].append(snap["streak_days"])
        sparklines["xp_earned"].append(snap["total_xp"])

    prev_discipline = sparklines["discipline_score"][5]
    prev_mindset = sparklines["mindset_strength"][5]
    prev_consistency = sparklines["consistency"][5]
    prev_growth = sparklines["growth_index"][5]
    prev_fin = sparklines["financial_goal"][5]
    prev_missions = sparklines["missions_completed"][5]
    prev_streak = sparklines["streak_days"][5]
    prev_xp = sparklines["xp_earned"][5]

    overall_metrics = {
        "discipline_score": current_overall["discipline_score"],
        "discipline_score_change": round(current_overall["discipline_score"] - prev_discipline, 1),
        "mindset_strength": current_overall["mindset_strength"],
        "mindset_strength_change": round(current_overall["mindset_strength"] - prev_mindset, 1),
        "consistency": current_overall["consistency"],
        "consistency_change": round(current_overall["consistency"] - prev_consistency, 1),
        "growth_index": current_overall["growth_index"],
        "growth_index_change": round(current_overall["growth_index"] - prev_growth, 1),
        "financial_goal": current_overall["financial_goal"],
        "financial_goal_change": round(current_overall["financial_goal"] - prev_fin, 1),
        "financial_goal_pct": current_overall["financial_goal"],
        "active_days": current_overall["active_days"],
        "current_streak": current_overall["current_streak"],
        "longest_streak": current_overall["longest_streak"],
        "streak_days": current_overall["current_streak"],
        "streak_days_change": current_overall["current_streak"] - prev_streak,
        "missions_completed_change": current_overall["completed_missions"] - prev_missions,
        "xp_earned": progression["total_xp"],
        "xp_earned_change": progression["total_xp"] - prev_xp,
        "progression": progression,
        "sparklines": sparklines,
        "mission_completion": {
            "completed": current_overall["completed_missions"],
            "total": current_overall["total_missions"],
            "percentage": (
                round((current_overall["completed_missions"] / current_overall["total_missions"]) * 100)
                if current_overall["total_missions"] > 0 else 0
            ),
        },
        "goals": {
            "total": current_overall["total_goals"],
            "completed": current_overall["completed_goals"],
            "active": current_overall["total_goals"] - current_overall["completed_goals"],
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

    return {
        "overall": overall_metrics,
        "daily": daily_progress,
    }

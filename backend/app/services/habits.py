import sqlite3
from datetime import datetime, date, timedelta
from typing import Dict, Any, List, Optional
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "app.db"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_demo_user_id() -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE email = ?", ("demo@masterykeycoach.com",))
    row = cursor.fetchone()
    conn.close()
    return row["id"] if row else 1


def validate_target_date(target_date_str: str) -> date:
    try:
        target_dt = datetime.strptime(target_date_str, "%Y-%m-%d").date()
    except ValueError:
        raise ValueError("Invalid date format. Expected YYYY-MM-DD.")

    today_dt = date.today()
    min_dt = today_dt - timedelta(days=7)

    if target_dt > today_dt:
        raise ValueError("Cannot log habit completions for future dates.")

    if target_dt < min_dt:
        raise ValueError("Cannot log habit completions older than 7 days.")

    return target_dt


def compute_habit_streaks(habit_id: int, user_id: int) -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT completed_date
        FROM habit_logs
        WHERE habit_id = ? AND user_id = ?
        ORDER BY completed_date DESC
        """,
        (habit_id, user_id),
    )
    rows = cursor.fetchall()
    conn.close()

    completed_dates_set = {r["completed_date"] for r in rows}

    today_dt = date.today()
    past_7_days = [(today_dt - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(6, -1, -1)]

    recent_7_days_log = [
        {"date": d, "completed": d in completed_dates_set}
        for d in past_7_days
    ]

    completed_7_count = sum(1 for d in past_7_days if d in completed_dates_set)
    weekly_completion_pct = round((completed_7_count / 7.0) * 100)

    # Current streak calculation (backwards from today or yesterday)
    today_str = today_dt.strftime("%Y-%m-%d")
    yesterday_str = (today_dt - timedelta(days=1)).strftime("%Y-%m-%d")

    current_streak = 0
    start_dt = None

    if today_str in completed_dates_set:
        start_dt = today_dt
    elif yesterday_str in completed_dates_set:
        start_dt = today_dt - timedelta(days=1)

    if start_dt:
        curr_eval_dt = start_dt
        while curr_eval_dt.strftime("%Y-%m-%d") in completed_dates_set:
            current_streak += 1
            curr_eval_dt -= timedelta(days=1)

    # Longest streak calculation
    sorted_dates = sorted([datetime.strptime(d, "%Y-%m-%d").date() for d in completed_dates_set])
    longest_streak = 0
    if sorted_dates:
        curr_streak = 1
        max_streak = 1
        for i in range(1, len(sorted_dates)):
            if sorted_dates[i] == sorted_dates[i - 1] + timedelta(days=1):
                curr_streak += 1
            else:
                curr_streak = 1
            if curr_streak > max_streak:
                max_streak = curr_streak
        longest_streak = max_streak

    return {
        "current_streak": current_streak,
        "longest_streak": max(longest_streak, current_streak),
        "weekly_completion_pct": weekly_completion_pct,
        "total_completions": len(completed_dates_set),
        "recent_7_days": recent_7_days_log,
    }


def get_user_habits(user_id: int) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, user_id, title, description, category, frequency, target_days_per_week, status, created_at
        FROM habits
        WHERE user_id = ? AND status = 'active'
        ORDER BY created_at ASC
        """,
        (user_id,),
    )
    rows = cursor.fetchall()
    conn.close()

    result = []
    for r in rows:
        habit_dict = dict(r)
        streaks_info = compute_habit_streaks(habit_dict["id"], user_id)
        habit_dict.update(streaks_info)
        result.append(habit_dict)

    return result


def get_habit_by_id(habit_id: int, user_id: int) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM habits WHERE id = ? AND user_id = ?",
        (habit_id, user_id),
    )
    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    habit_dict = dict(row)
    streaks_info = compute_habit_streaks(habit_id, user_id)
    habit_dict.update(streaks_info)
    return habit_dict


def create_habit(user_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
    title = data.get("title")
    if not title or not title.strip():
        raise ValueError("Habit title is required.")

    description = data.get("description", "")
    category = data.get("category", "general")
    frequency = data.get("frequency", "daily")
    target_days_per_week = data.get("target_days_per_week", 7)

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO habits (user_id, title, description, category, frequency, target_days_per_week, status)
        VALUES (?, ?, ?, ?, ?, ?, 'active')
        """,
        (user_id, title.strip(), description, category, frequency, target_days_per_week),
    )
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()

    return get_habit_by_id(new_id, user_id)


def update_habit(habit_id: int, user_id: int, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    existing = get_habit_by_id(habit_id, user_id)
    if not existing:
        return None

    title = data.get("title", existing["title"])
    description = data.get("description", existing["description"])
    category = data.get("category", existing["category"])
    frequency = data.get("frequency", existing["frequency"])
    target_days_per_week = data.get("target_days_per_week", existing["target_days_per_week"])
    status = data.get("status", existing["status"])

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE habits
        SET title = ?, description = ?, category = ?, frequency = ?, target_days_per_week = ?, status = ?
        WHERE id = ? AND user_id = ?
        """,
        (title.strip(), description, category, frequency, target_days_per_week, status, habit_id, user_id),
    )
    conn.commit()
    conn.close()

    return get_habit_by_id(habit_id, user_id)


def delete_habit(habit_id: int, user_id: int) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM habit_logs WHERE habit_id = ? AND user_id = ?", (habit_id, user_id))
    cursor.execute("DELETE FROM habits WHERE id = ? AND user_id = ?", (habit_id, user_id))
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    return affected > 0


def toggle_habit_log(habit_id: int, user_id: int, target_date_str: str) -> Dict[str, Any]:
    # 1. Validate date window (today and previous 7 days only)
    validated_dt = validate_target_date(target_date_str)
    date_str = validated_dt.strftime("%Y-%m-%d")

    # 2. Check if habit exists for user
    habit = get_habit_by_id(habit_id, user_id)
    if not habit:
        raise KeyError(f"Habit with ID {habit_id} not found.")

    conn = get_connection()
    cursor = conn.cursor()

    # Check if completion log exists
    cursor.execute(
        "SELECT id FROM habit_logs WHERE habit_id = ? AND user_id = ? AND completed_date = ?",
        (habit_id, user_id, date_str),
    )
    log_row = cursor.fetchone()

    toggled_status = False
    if log_row:
        # Log exists -> uncheck / delete
        cursor.execute("DELETE FROM habit_logs WHERE id = ?", (log_row["id"],))
        toggled_status = False
    else:
        # Log absent -> check / insert with UNIQUE constraint safety
        cursor.execute(
            "INSERT INTO habit_logs (habit_id, user_id, completed_date) VALUES (?, ?, ?)",
            (habit_id, user_id, date_str),
        )
        toggled_status = True

    conn.commit()
    conn.close()

    updated_habit = get_habit_by_id(habit_id, user_id)
    return {
        "toggled_date": date_str,
        "completed": toggled_status,
        "habit": updated_habit,
    }


def get_aggregate_habit_stats(user_id: int) -> Dict[str, Any]:
    habits = get_user_habits(user_id)
    if not habits:
        return {
            "total_active_habits": 0,
            "avg_current_streak": 0,
            "max_longest_streak": 0,
            "overall_7day_completion_pct": 0,
            "habits_completed_today": 0,
        }

    today_str = date.today().strftime("%Y-%m-%d")

    total_habits = len(habits)
    avg_streak = round(sum(h["current_streak"] for h in habits) / total_habits, 1)
    max_streak = max(h["longest_streak"] for h in habits)
    avg_weekly_pct = round(sum(h["weekly_completion_pct"] for h in habits) / total_habits)

    completed_today = sum(
        1 for h in habits
        if any(d["date"] == today_str and d["completed"] for d in h["recent_7_days"])
    )

    return {
        "total_active_habits": total_habits,
        "avg_current_streak": avg_streak,
        "max_longest_streak": max_streak,
        "overall_7day_completion_pct": avg_weekly_pct,
        "habits_completed_today": completed_today,
    }

import sqlite3
from typing import Any, Dict

from ..database import get_connection


def format_settings_row(row: Any) -> Dict[str, Any]:
    s_dict = dict(row)
    s_dict["notifications_enabled"] = bool(s_dict["notifications_enabled"])
    return s_dict


def get_or_create_user_settings(user_id: int) -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM user_settings WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()

    if not row:
        cursor.execute(
            """
            INSERT INTO user_settings (user_id, theme, notifications_enabled, coach_style, daily_reminder_time, profile_visibility)
            VALUES (?, 'dark', 1, 'strategic', '08:00', 'public')
            """,
            (user_id,),
        )
        conn.commit()
        cursor.execute("SELECT * FROM user_settings WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()

    conn.close()
    return format_settings_row(row)


def update_user_settings(user_id: int, updates: Dict[str, Any]) -> Dict[str, Any]:
    get_or_create_user_settings(user_id)

    valid_fields = ["theme", "notifications_enabled", "coach_style", "daily_reminder_time", "profile_visibility"]
    filtered_updates = {k: v for k, v in updates.items() if k in valid_fields and v is not None}

    if not filtered_updates:
        return get_or_create_user_settings(user_id)

    set_clauses = []
    params = []

    for key, value in filtered_updates.items():
        if key == "notifications_enabled":
            value = 1 if value else 0
        set_clauses.append(f"{key} = ?")
        params.append(value)

    set_clauses.append("updated_at = CURRENT_TIMESTAMP")
    params.append(user_id)

    sql = f"UPDATE user_settings SET {', '.join(set_clauses)} WHERE user_id = ?"

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(sql, params)
    conn.commit()

    cursor.execute("SELECT * FROM user_settings WHERE user_id = ?", (user_id,))
    updated_row = cursor.fetchone()
    conn.close()

    return format_settings_row(updated_row)

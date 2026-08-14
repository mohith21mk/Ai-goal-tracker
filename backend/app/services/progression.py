import math
from datetime import datetime, date, timedelta
from typing import Any, Dict, List, Optional

from ..database import get_connection


def calculate_user_xp(user_id: int) -> Dict[str, int]:
    """
    Calculate server-authoritative XP for a user from real database records.
    - Completed Missions: SUM(xp_reward) for missions where completed = 1 and completed_at is not null
    - Completed Habits: 15 XP per verified habit_logs row
    """
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Mission XP
    cursor.execute(
        """
        SELECT COALESCE(SUM(xp_reward), 0)
        FROM missions
        WHERE user_id = ? AND completed = 1 AND completed_at IS NOT NULL
        """,
        (user_id,),
    )
    mission_row = cursor.fetchone()
    mission_xp = int(mission_row[0] if mission_row and mission_row[0] is not None else 0)

    # 2. Habit XP (15 XP per verified log)
    cursor.execute(
        """
        SELECT COUNT(*)
        FROM habit_logs
        WHERE user_id = ?
        """,
        (user_id,),
    )
    habit_count_row = cursor.fetchone()
    habit_count = int(habit_count_row[0] if habit_count_row else 0)
    habit_xp = habit_count * 15

    conn.close()

    total_xp = mission_xp + habit_xp

    return {
        "mission_xp": mission_xp,
        "habit_xp": habit_xp,
        "total_xp": total_xp,
    }


def calculate_level(total_xp: int) -> int:
    """
    Centralized Level Formula:
    level = floor(total_xp / 500) + 1

    Examples:
    0 XP    -> Level 1
    499 XP  -> Level 1
    500 XP  -> Level 2
    999 XP  -> Level 2
    1000 XP -> Level 3
    """
    if total_xp < 0:
        total_xp = 0
    return (total_xp // 500) + 1


def calculate_rank(level: int) -> str:
    """
    Centralized Rank Tiers:
    Level 1–5:   INITIATE
    Level 6–10:  ADEPT
    Level 11–20: MASTER
    Level 21–50: LEGEND
    Level 51+:   MASTERY SOVEREIGN
    """
    if level <= 5:
        return "INITIATE"
    elif level <= 10:
        return "ADEPT"
    elif level <= 20:
        return "MASTER"
    elif level <= 50:
        return "LEGEND"
    else:
        return "MASTERY SOVEREIGN"


def get_user_progression(user_id: int) -> Dict[str, Any]:
    """
    Returns consolidated progression state for a user.
    """
    xp_data = calculate_user_xp(user_id)
    total_xp = xp_data["total_xp"]
    level = calculate_level(total_xp)
    rank = calculate_rank(level)

    next_level_xp = level * 500
    xp_into_current_level = total_xp - ((level - 1) * 500)
    xp_to_next_level = max(0, next_level_xp - total_xp)
    level_progress_percent = round((xp_into_current_level / 500.0) * 100, 2)

    return {
        "total_xp": total_xp,
        "mission_xp": xp_data["mission_xp"],
        "habit_xp": xp_data["habit_xp"],
        "level": level,
        "rank": rank,
        "xp_to_next_level": xp_to_next_level,
        "level_progress_percent": level_progress_percent,
    }


def get_user_max_habit_streak(user_id: int) -> int:
    """
    Calculate server-authoritative maximum consecutive continuous habit streak.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT DISTINCT completed_date
        FROM habit_logs
        WHERE user_id = ?
        ORDER BY completed_date ASC
        """,
        (user_id,),
    )
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return 0

    dates = []
    for r in rows:
        try:
            d = datetime.strptime(r["completed_date"], "%Y-%m-%d").date()
            dates.append(d)
        except (ValueError, TypeError):
            continue

    if not dates:
        return 0

    max_streak = 1
    current_streak = 1
    for i in range(1, len(dates)):
        if dates[i] == dates[i - 1] + timedelta(days=1):
            current_streak += 1
        elif dates[i] > dates[i - 1] + timedelta(days=1):
            current_streak = 1
        if current_streak > max_streak:
            max_streak = current_streak

    return max_streak


def list_user_credentials(user_id: int) -> List[Dict[str, Any]]:
    """
    Fetch all credentials earned by a user.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, user_id, credential_type, slug, title, description, tier, xp_value, evidence_type, evidence_id, issued_at
        FROM user_credentials
        WHERE user_id = ?
        ORDER BY issued_at ASC
        """,
        (user_id,),
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def evaluate_and_issue_credentials(user_id: int) -> Dict[str, Any]:
    """
    Evaluate server-authoritative database records against credential milestone criteria.
    Issues any newly qualified credentials. Never trusts client claims.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Authoritative Evidence Gathering
    max_streak = get_user_max_habit_streak(user_id)

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM missions
        WHERE user_id = ? AND completed = 1 AND completed_at IS NOT NULL
        """,
        (user_id,),
    )
    mission_count_row = cursor.fetchone()
    completed_missions = int(mission_count_row[0] if mission_count_row else 0)

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM blueprint_milestones bm
        JOIN life_blueprints lb ON bm.blueprint_id = lb.id
        WHERE lb.user_id = ? AND bm.completed = 1 AND bm.completed_at IS NOT NULL
        """,
        (user_id,),
    )
    milestone_count_row = cursor.fetchone()
    completed_milestones = int(milestone_count_row[0] if milestone_count_row else 0)

    progression = get_user_progression(user_id)
    current_level = progression["level"]

    # 2. Existing Credentials Check
    cursor.execute(
        "SELECT slug FROM user_credentials WHERE user_id = ?",
        (user_id,),
    )
    existing_slugs = {r["slug"] for r in cursor.fetchall()}

    # 3. Rule Definitions
    rules = [
        {
            "slug": "streak_7",
            "condition": max_streak >= 7,
            "credential_type": "streak_badge",
            "title": "7-Day Discipline Initiate",
            "description": "Verified continuous 7-day habit execution streak.",
            "tier": "bronze",
            "xp_value": 50,
            "evidence_type": "habit_streak",
            "evidence_id": str(max_streak),
        },
        {
            "slug": "streak_30",
            "condition": max_streak >= 30,
            "credential_type": "streak_badge",
            "title": "30-Day Momentum Vanguard",
            "description": "Verified continuous 30-day habit execution streak.",
            "tier": "silver",
            "xp_value": 150,
            "evidence_type": "habit_streak",
            "evidence_id": str(max_streak),
        },
        {
            "slug": "streak_100",
            "condition": max_streak >= 100,
            "credential_type": "streak_badge",
            "title": "100-Day Iron Discipline",
            "description": "Verified continuous 100-day habit execution streak.",
            "tier": "gold",
            "xp_value": 500,
            "evidence_type": "habit_streak",
            "evidence_id": str(max_streak),
        },
        {
            "slug": "missions_50",
            "condition": completed_missions >= 50,
            "credential_type": "mission_badge",
            "title": "Protocol Execution Master",
            "description": "Successfully executed and verified 50 completed missions.",
            "tier": "silver",
            "xp_value": 200,
            "evidence_type": "mission_count",
            "evidence_id": str(completed_missions),
        },
        {
            "slug": "blueprint_milestone_1",
            "condition": completed_milestones >= 1,
            "credential_type": "blueprint_badge",
            "title": "Blueprint Architect",
            "description": "Successfully executed a verified Life Blueprint strategic milestone.",
            "tier": "bronze",
            "xp_value": 100,
            "evidence_type": "milestone_completed",
            "evidence_id": str(completed_milestones),
        },
        {
            "slug": "mastery_level_20",
            "condition": current_level >= 20,
            "credential_type": "mastery_badge",
            "title": "Mastery Sovereign Rank",
            "description": "Attained Master rank with verified server level 20 or above.",
            "tier": "gold",
            "xp_value": 1000,
            "evidence_type": "mastery_level",
            "evidence_id": str(current_level),
        },
    ]

    newly_earned = []
    for rule in rules:
        if rule["condition"] and rule["slug"] not in existing_slugs:
            cursor.execute(
                """
                INSERT INTO user_credentials (user_id, credential_type, slug, title, description, tier, xp_value, evidence_type, evidence_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    rule["credential_type"],
                    rule["slug"],
                    rule["title"],
                    rule["description"],
                    rule["tier"],
                    rule["xp_value"],
                    rule["evidence_type"],
                    rule["evidence_id"],
                ),
            )
            cred_id = cursor.lastrowid
            cursor.execute("SELECT * FROM user_credentials WHERE id = ?", (cred_id,))
            new_cred = dict(cursor.fetchone())
            newly_earned.append(new_cred)
            existing_slugs.add(rule["slug"])

    conn.commit()

    cursor.execute(
        """
        SELECT id, user_id, credential_type, slug, title, description, tier, xp_value, evidence_type, evidence_id, issued_at
        FROM user_credentials
        WHERE user_id = ?
        ORDER BY issued_at ASC
        """,
        (user_id,),
    )
    all_credentials = [dict(r) for r in cursor.fetchall()]
    conn.close()

    return {
        "newly_earned": newly_earned,
        "credentials": all_credentials,
    }

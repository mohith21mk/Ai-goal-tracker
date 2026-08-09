import datetime
from typing import Any, Dict, List, Optional

from ..database import get_connection


def list_blueprints(user_id: int) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT * FROM life_blueprints
        WHERE user_id = ?
        ORDER BY CASE WHEN status = 'active' THEN 0 ELSE 1 END, created_at DESC
        """,
        (user_id,),
    )
    rows = cursor.fetchall()
    blueprints = [dict(r) for r in rows]
    conn.close()
    return blueprints


def get_blueprint(user_id: int, blueprint_id: int) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM life_blueprints WHERE id = ? AND user_id = ?",
        (blueprint_id, user_id),
    )
    bp_row = cursor.fetchone()
    if not bp_row:
        conn.close()
        return None

    bp = dict(bp_row)

    # Fetch Life Areas
    cursor.execute(
        "SELECT * FROM blueprint_areas WHERE blueprint_id = ? AND user_id = ? ORDER BY position ASC",
        (blueprint_id, user_id),
    )
    bp["areas"] = [dict(a) for a in cursor.fetchall()]

    # Fetch Phases
    cursor.execute(
        "SELECT * FROM blueprint_phases WHERE blueprint_id = ? ORDER BY phase_number ASC, position ASC",
        (blueprint_id,),
    )
    phases = [dict(p) for p in cursor.fetchall()]

    total_bp_milestones = 0
    completed_bp_milestones = 0

    for phase in phases:
        cursor.execute(
            "SELECT * FROM blueprint_milestones WHERE phase_id = ? ORDER BY position ASC",
            (phase["id"],),
        )
        milestones = [dict(m) for m in cursor.fetchall()]
        phase["milestones"] = milestones

        phase_total = len(milestones)
        phase_completed = sum(1 for m in milestones if m["completed"] == 1)
        phase["total_milestones"] = phase_total
        phase["completed_milestones"] = phase_completed
        phase["progress_percentage"] = round((phase_completed / phase_total) * 100) if phase_total > 0 else 0

        total_bp_milestones += phase_total
        completed_bp_milestones += phase_completed

    bp["phases"] = phases
    bp["total_milestones"] = total_bp_milestones
    bp["completed_milestones"] = completed_bp_milestones
    bp["progress_percentage"] = round((completed_bp_milestones / total_bp_milestones) * 100) if total_bp_milestones > 0 else 0

    conn.close()
    return bp


def get_active_blueprint(user_id: int) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id FROM life_blueprints WHERE user_id = ? AND status = 'active' ORDER BY updated_at DESC LIMIT 1",
        (user_id,),
    )
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    return get_blueprint(user_id, row["id"])


def create_blueprint(
    user_id: int,
    title: str,
    description: Optional[str] = None,
    vision: Optional[str] = None,
    target_date: Optional[str] = None,
    set_active: bool = True,
) -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor()

    if set_active:
        cursor.execute(
            "UPDATE life_blueprints SET status = 'archived', updated_at = CURRENT_TIMESTAMP WHERE user_id = ? AND status = 'active'",
            (user_id,),
        )

    status = "active" if set_active else "pending"
    cursor.execute(
        """
        INSERT INTO life_blueprints (user_id, title, description, vision, target_date, status)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (user_id, title, description, vision, target_date, status),
    )
    conn.commit()
    bp_id = cursor.lastrowid
    conn.close()
    return get_blueprint(user_id, bp_id)


def update_blueprint(
    user_id: int,
    blueprint_id: int,
    title: Optional[str] = None,
    description: Optional[str] = None,
    vision: Optional[str] = None,
    target_date: Optional[str] = None,
    status: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM life_blueprints WHERE id = ? AND user_id = ?", (blueprint_id, user_id))
    if not cursor.fetchone():
        conn.close()
        return None

    fields = []
    values = []
    if title is not None:
        fields.append("title = ?")
        values.append(title)
    if description is not None:
        fields.append("description = ?")
        values.append(description)
    if vision is not None:
        fields.append("vision = ?")
        values.append(vision)
    if target_date is not None:
        fields.append("target_date = ?")
        values.append(target_date)
    if status is not None:
        fields.append("status = ?")
        values.append(status)

    if fields:
        fields.append("updated_at = CURRENT_TIMESTAMP")
        values.extend([blueprint_id, user_id])
        cursor.execute(
            f"UPDATE life_blueprints SET {', '.join(fields)} WHERE id = ? AND user_id = ?",
            values,
        )
        conn.commit()

    conn.close()
    return get_blueprint(user_id, blueprint_id)


def activate_blueprint(user_id: int, blueprint_id: int) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM life_blueprints WHERE id = ? AND user_id = ?", (blueprint_id, user_id))
    if not cursor.fetchone():
        conn.close()
        return None

    # Atomic transaction: Archive all user blueprints, set targeted to active
    cursor.execute(
        "UPDATE life_blueprints SET status = 'archived', updated_at = CURRENT_TIMESTAMP WHERE user_id = ?",
        (user_id,),
    )
    cursor.execute(
        "UPDATE life_blueprints SET status = 'active', updated_at = CURRENT_TIMESTAMP WHERE id = ? AND user_id = ?",
        (blueprint_id, user_id),
    )
    conn.commit()
    conn.close()

    return get_blueprint(user_id, blueprint_id)


def delete_blueprint(user_id: int, blueprint_id: int) -> bool:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM life_blueprints WHERE id = ? AND user_id = ?", (blueprint_id, user_id))
    if not cursor.fetchone():
        conn.close()
        return False

    cursor.execute("DELETE FROM life_blueprints WHERE id = ? AND user_id = ?", (blueprint_id, user_id))
    conn.commit()
    conn.close()
    return True


# -------------------------------------------------------------------
# Phases & Milestones CRUD
# -------------------------------------------------------------------

def create_phase(
    user_id: int,
    blueprint_id: int,
    title: str,
    description: Optional[str] = None,
    phase_number: Optional[int] = None,
    area_id: Optional[int] = None,
) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM life_blueprints WHERE id = ? AND user_id = ?", (blueprint_id, user_id))
    if not cursor.fetchone():
        conn.close()
        return None

    if phase_number is None:
        cursor.execute("SELECT MAX(phase_number) FROM blueprint_phases WHERE blueprint_id = ?", (blueprint_id,))
        max_num = cursor.fetchone()[0]
        phase_number = (max_num or 0) + 1

    cursor.execute(
        """
        INSERT INTO blueprint_phases (blueprint_id, area_id, title, description, phase_number, status, position)
        VALUES (?, ?, ?, ?, ?, 'pending', ?)
        """,
        (blueprint_id, area_id, title, description, phase_number, phase_number),
    )
    conn.commit()
    phase_id = cursor.lastrowid
    conn.close()

    return get_blueprint(user_id, blueprint_id)


def update_phase(
    user_id: int,
    phase_id: int,
    title: Optional[str] = None,
    description: Optional[str] = None,
    status: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT p.id, p.blueprint_id FROM blueprint_phases p
        JOIN life_blueprints b ON p.blueprint_id = b.id
        WHERE p.id = ? AND b.user_id = ?
        """,
        (phase_id, user_id),
    )
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None

    blueprint_id = row["blueprint_id"]
    fields = []
    values = []
    if title is not None:
        fields.append("title = ?")
        values.append(title)
    if description is not None:
        fields.append("description = ?")
        values.append(description)
    if status is not None:
        fields.append("status = ?")
        values.append(status)

    if fields:
        fields.append("updated_at = CURRENT_TIMESTAMP")
        values.append(phase_id)
        cursor.execute(f"UPDATE blueprint_phases SET {', '.join(fields)} WHERE id = ?", values)
        conn.commit()

    conn.close()
    return get_blueprint(user_id, blueprint_id)


def delete_phase(user_id: int, phase_id: int) -> bool:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT p.id FROM blueprint_phases p
        JOIN life_blueprints b ON p.blueprint_id = b.id
        WHERE p.id = ? AND b.user_id = ?
        """,
        (phase_id, user_id),
    )
    if not cursor.fetchone():
        conn.close()
        return False

    cursor.execute("DELETE FROM blueprint_phases WHERE id = ?", (phase_id,))
    conn.commit()
    conn.close()
    return True


def create_milestone(
    user_id: int,
    phase_id: int,
    title: str,
    description: Optional[str] = None,
    target_date: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT p.id, p.blueprint_id FROM blueprint_phases p
        JOIN life_blueprints b ON p.blueprint_id = b.id
        WHERE p.id = ? AND b.user_id = ?
        """,
        (phase_id, user_id),
    )
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None

    blueprint_id = row["blueprint_id"]
    cursor.execute("SELECT MAX(position) FROM blueprint_milestones WHERE phase_id = ?", (phase_id,))
    max_pos = cursor.fetchone()[0]
    position = (max_pos or 0) + 1

    cursor.execute(
        """
        INSERT INTO blueprint_milestones (phase_id, blueprint_id, title, description, target_date, completed, position)
        VALUES (?, ?, ?, ?, ?, 0, ?)
        """,
        (phase_id, blueprint_id, title, description, target_date, position),
    )
    conn.commit()
    conn.close()

    return get_blueprint(user_id, blueprint_id)


def toggle_milestone(user_id: int, milestone_id: int) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT m.id, m.phase_id, m.blueprint_id, m.completed, m.title, p.title as phase_title
        FROM blueprint_milestones m
        JOIN life_blueprints b ON m.blueprint_id = b.id
        JOIN blueprint_phases p ON m.phase_id = p.id
        WHERE m.id = ? AND b.user_id = ?
        """,
        (milestone_id, user_id),
    )
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None

    blueprint_id = row["blueprint_id"]
    phase_id = row["phase_id"]
    was_completed = bool(row["completed"])
    new_completed = 0 if was_completed else 1
    completed_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") if new_completed == 1 else None

    cursor.execute(
        """
        UPDATE blueprint_milestones
        SET completed = ?, completed_at = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (new_completed, completed_at, milestone_id),
    )
    conn.commit()

    # XP System Integration:
    # 1. Award +50 XP upon milestone completion (only when completing for the first time)
    # 2. Check if phase becomes fully completed for the first time, award +200 XP
    if new_completed == 1 and not was_completed:
        # Create a mission completion record if appropriate or record in XP
        cursor.execute(
            """
            INSERT INTO missions (title, description, category, time, difficulty, xp_reward, completed, user_id, completed_at)
            VALUES (?, ?, 'blueprint', 'Milestone', 'hard', 50, 1, ?, CURRENT_TIMESTAMP)
            """,
            (f"Milestone Achieved: {row['title']}", f"Completed milestone in {row['phase_title']}", user_id),
        )
        conn.commit()

        # Check phase completion
        cursor.execute("SELECT COUNT(*) FROM blueprint_milestones WHERE phase_id = ? AND completed = 0", (phase_id,))
        uncompleted_in_phase = cursor.fetchone()[0]

        if uncompleted_in_phase == 0:
            # Mark phase status = 'completed'
            cursor.execute("UPDATE blueprint_phases SET status = 'completed', updated_at = CURRENT_TIMESTAMP WHERE id = ?", (phase_id,))
            conn.commit()

            # Award +200 XP for Phase Completion
            cursor.execute(
                """
                INSERT INTO missions (title, description, category, time, difficulty, xp_reward, completed, user_id, completed_at)
                VALUES (?, ?, 'blueprint', 'Phase Mastery', 'hard', 200, 1, ?, CURRENT_TIMESTAMP)
                """,
                (f"Phase Mastered: {row['phase_title']}", "Completed all strategic milestones in phase", user_id),
            )
            conn.commit()

    conn.close()
    return get_blueprint(user_id, blueprint_id)


def delete_milestone(user_id: int, milestone_id: int) -> bool:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT m.id FROM blueprint_milestones m
        JOIN life_blueprints b ON m.blueprint_id = b.id
        WHERE m.id = ? AND b.user_id = ?
        """,
        (milestone_id, user_id),
    )
    if not cursor.fetchone():
        conn.close()
        return False

    # Unlink goals associated with this milestone
    cursor.execute("UPDATE goals SET milestone_id = NULL WHERE milestone_id = ?", (milestone_id,))
    cursor.execute("DELETE FROM blueprint_milestones WHERE id = ?", (milestone_id,))
    conn.commit()
    conn.close()
    return True


def get_blueprint_telemetry(user_id: int) -> Optional[Dict[str, Any]]:
    bp = get_active_blueprint(user_id)
    if not bp:
        return {
            "active_blueprint_id": None,
            "title": "No Active Blueprint",
            "current_phase": "None",
            "completed_milestones": 0,
            "total_milestones": 0,
            "progress_percentage": 0,
            "next_milestone": "Define your Life Blueprint",
            "target_date": None,
        }

    active_phase_name = "Phase 1"
    next_milestone_title = "None"

    # Find active phase
    active_phase = next((p for p in bp["phases"] if p["status"] == "active"), None)
    if not active_phase and bp["phases"]:
        active_phase = bp["phases"][0]

    if active_phase:
        active_phase_name = active_phase["title"]
        next_m = next((m for m in active_phase["milestones"] if m["completed"] == 0), None)
        if next_m:
            next_milestone_title = next_m["title"]

    return {
        "active_blueprint_id": bp["id"],
        "title": bp["title"],
        "current_phase": active_phase_name,
        "completed_milestones": bp["completed_milestones"],
        "total_milestones": bp["total_milestones"],
        "progress_percentage": bp["progress_percentage"],
        "next_milestone": next_milestone_title,
        "target_date": bp["target_date"],
    }

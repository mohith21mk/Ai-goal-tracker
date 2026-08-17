from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from ..database import get_connection
from .logger import logger
from .notifications import create_notification

VALID_CATEGORIES = {
    "Bug",
    "Feature Request",
    "UI/UX",
    "Performance",
    "Account/Login",
    "Community/Chat",
    "AI Coach",
    "Credential",
    "Other"
}

VALID_SEVERITIES = {
    "Low",
    "Normal",
    "High",
    "Critical"
}

VALID_STATUSES = {
    "new",
    "reviewing",
    "resolved",
    "closed"
}


def sanitize_text(text: Optional[str]) -> str:
    """Strip and sanitize text input."""
    if not text:
        return ""
    return text.strip()


async def create_feedback(
    user_id: int,
    category: str,
    message: str,
    severity: str = "Normal",
    page_url: Optional[str] = None,
    user_agent: Optional[str] = None
) -> Dict[str, Any]:
    """
    Submits user feedback into the database and creates notifications for system admins.
    """
    category_clean = sanitize_text(category)
    message_clean = sanitize_text(message)
    severity_clean = sanitize_text(severity) or "Normal"

    if category_clean not in VALID_CATEGORIES:
        raise ValueError(f"Invalid feedback category: '{category_clean}'. Must be one of {sorted(VALID_CATEGORIES)}")

    if severity_clean not in VALID_SEVERITIES:
        raise ValueError(f"Invalid severity level: '{severity_clean}'. Must be one of {sorted(VALID_SEVERITIES)}")

    if not message_clean or len(message_clean) < 3:
        raise ValueError("Feedback message must contain at least 3 characters.")

    if len(message_clean) > 5000:
        raise ValueError("Feedback message cannot exceed 5000 characters.")

    now_dt = datetime.now(timezone.utc)
    now_str = now_dt.strftime("%Y-%m-%d %H:%M:%S")

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO feedback (user_id, category, message, severity, status, page_url, user_agent, created_at, updated_at)
        VALUES (?, ?, ?, ?, 'new', ?, ?, ?, ?)
        """,
        (user_id, category_clean, message_clean, severity_clean, page_url, user_agent, now_str, now_str)
    )
    feedback_id = cursor.lastrowid
    conn.commit()

    # Find all admin users to dispatch notification
    try:
        cursor.execute("SELECT id FROM users WHERE role = 'admin' AND (is_active IS NULL OR is_active = 1)")
        admin_rows = cursor.fetchall()
        for admin in admin_rows:
            admin_id = admin["id"] if isinstance(admin, dict) or hasattr(admin, "__getitem__") else admin[0]
            await create_notification(
                user_id=admin_id,
                type="admin_feedback",
                title="New User Feedback Received",
                message=f"[{category_clean}] ({severity_clean}): {message_clean[:120]}",
                reference_type="feedback",
                reference_id=feedback_id,
                data={
                    "category": category_clean,
                    "severity": severity_clean,
                    "feedback_id": feedback_id
                }
            )
    except Exception as err:
        logger.debug(f"Admin notification dispatch error: {err}")

    conn.close()

    return {
        "id": feedback_id,
        "user_id": user_id,
        "category": category_clean,
        "message": message_clean,
        "severity": severity_clean,
        "status": "new",
        "created_at": now_str
    }


def get_feedback_by_id(feedback_id: int) -> Optional[Dict[str, Any]]:
    """Retrieve single feedback item with submitter profile metadata for administrators."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT f.*, u.email as user_email, u.full_name as user_full_name, u.username as user_username, u.mkc_id as user_mkc_id
        FROM feedback f
        LEFT JOIN users u ON u.id = f.user_id
        WHERE f.id = ?
        """,
        (feedback_id,)
    )
    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    return dict(row)


def list_feedback(
    limit: int = 50,
    offset: int = 0,
    category: Optional[str] = None,
    status: Optional[str] = None,
    severity: Optional[str] = None
) -> Tuple[List[Dict[str, Any]], int]:
    """List feedback with optional category/status/severity filters for administrators."""
    conn = get_connection()
    cursor = conn.cursor()

    where_clauses = []
    params = []

    if category:
        where_clauses.append("f.category = ?")
        params.append(category)
    if status:
        where_clauses.append("f.status = ?")
        params.append(status)
    if severity:
        where_clauses.append("f.severity = ?")
        params.append(severity)

    where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

    # Total count
    cursor.execute(f"SELECT COUNT(*) FROM feedback f {where_sql}", tuple(params))
    total_count = cursor.fetchone()[0]

    # Paginated rows
    query_sql = f"""
        SELECT f.*, u.email as user_email, u.full_name as user_full_name, u.username as user_username, u.mkc_id as user_mkc_id
        FROM feedback f
        LEFT JOIN users u ON u.id = f.user_id
        {where_sql}
        ORDER BY f.created_at DESC
        LIMIT ? OFFSET ?
    """
    cursor.execute(query_sql, tuple(params + [limit, offset]))
    rows = cursor.fetchall()
    conn.close()

    return [dict(r) for r in rows], total_count


def update_feedback(
    feedback_id: int,
    status: Optional[str] = None,
    severity: Optional[str] = None,
    admin_notes: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """Update feedback status, severity, and private admin notes."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id, status FROM feedback WHERE id = ?", (feedback_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None

    now_dt = datetime.now(timezone.utc)
    now_str = now_dt.strftime("%Y-%m-%d %H:%M:%S")

    updates = ["updated_at = ?"]
    params = [now_str]

    if status:
        status_clean = status.strip().lower()
        if status_clean not in VALID_STATUSES:
            conn.close()
            raise ValueError(f"Invalid status: '{status_clean}'. Must be one of {sorted(VALID_STATUSES)}")
        updates.append("status = ?")
        params.append(status_clean)
        if status_clean in ("resolved", "closed"):
            updates.append("resolved_at = ?")
            params.append(now_str)
        else:
            updates.append("resolved_at = NULL")

    if severity:
        sev_clean = severity.strip()
        if sev_clean not in VALID_SEVERITIES:
            conn.close()
            raise ValueError(f"Invalid severity: '{sev_clean}'. Must be one of {sorted(VALID_SEVERITIES)}")
        updates.append("severity = ?")
        params.append(sev_clean)

    if admin_notes is not None:
        updates.append("admin_notes = ?")
        params.append(admin_notes.strip())

    params.append(feedback_id)
    update_sql = f"UPDATE feedback SET {', '.join(updates)} WHERE id = ?"
    cursor.execute(update_sql, tuple(params))
    conn.commit()

    cursor.execute(
        """
        SELECT f.*, u.email as user_email, u.full_name as user_full_name, u.username as user_username, u.mkc_id as user_mkc_id
        FROM feedback f
        LEFT JOIN users u ON u.id = f.user_id
        WHERE f.id = ?
        """,
        (feedback_id,)
    )
    updated = cursor.fetchone()
    conn.close()

    return dict(updated) if updated else None


def delete_feedback(feedback_id: int) -> bool:
    """Delete a feedback entry (Admin only)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM feedback WHERE id = ?", (feedback_id,))
    if not cursor.fetchone():
        conn.close()
        return False

    cursor.execute("DELETE FROM feedback WHERE id = ?", (feedback_id,))
    conn.commit()
    conn.close()
    return True


def get_feedback_stats() -> Dict[str, Any]:
    """Aggregate statistics for admin dashboard."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM feedback")
    total = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM feedback WHERE status = 'new'")
    new_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM feedback WHERE status = 'reviewing'")
    reviewing = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM feedback WHERE status = 'resolved'")
    resolved = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM feedback WHERE status = 'closed'")
    closed = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM feedback WHERE severity = 'Critical' AND status IN ('new', 'reviewing')")
    critical_open = cursor.fetchone()[0]

    conn.close()

    return {
        "total": total,
        "new": new_count,
        "reviewing": reviewing,
        "resolved": resolved,
        "closed": closed,
        "critical_open": critical_open
    }

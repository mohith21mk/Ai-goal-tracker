from typing import Any, Dict, List, Optional
from ..database import get_connection
from .realtime import publish_notification_event


async def create_notification(
    user_id: int,
    type: str,
    title: str,
    message: str,
    reference_type: Optional[str] = None,
    reference_id: Optional[int] = None
) -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO notifications (user_id, type, title, message, reference_type, reference_id)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (user_id, type, title, message, reference_type, reference_id))
    
    notification_id = cursor.lastrowid
    conn.commit()

    cursor.execute(
        """
        SELECT id, user_id, type, title, message, reference_type, reference_id, is_read, created_at 
        FROM notifications WHERE id = ?
        """,
        (notification_id,)
    )
    notif = dict(cursor.fetchone())
    conn.close()
    
    # Broadcast to recipient in real-time via Redis / local WS
    await publish_notification_event(user_id, notif)
    
    return notif


def get_user_notifications(user_id: int, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, type, title, message, reference_type, reference_id, is_read, created_at 
        FROM notifications 
        WHERE user_id = ? 
        ORDER BY created_at DESC 
        LIMIT ? OFFSET ?
        """,
        (user_id, limit, offset)
    )
    notifications = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return notifications


def get_unread_notification_count(user_id: int) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM notifications WHERE user_id = ? AND is_read = 0", (user_id,))
    count = cursor.fetchone()[0]
    conn.close()
    return count


def mark_notification_read(user_id: int, notification_id: int) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM notifications WHERE id = ? AND user_id = ?", (notification_id, user_id))
    if not cursor.fetchone():
        conn.close()
        return False

    cursor.execute("UPDATE notifications SET is_read = 1 WHERE id = ? AND user_id = ?", (notification_id, user_id))
    conn.commit()
    conn.close()
    return True


def mark_all_notifications_read(user_id: int) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE notifications SET is_read = 1 WHERE user_id = ? AND is_read = 0", (user_id,))
    updated_count = cursor.rowcount
    conn.commit()
    conn.close()
    return updated_count


def delete_notification(user_id: int, notification_id: int) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM notifications WHERE id = ? AND user_id = ?", (notification_id, user_id))
    if not cursor.fetchone():
        conn.close()
        return False

    cursor.execute("DELETE FROM notifications WHERE id = ? AND user_id = ?", (notification_id, user_id))
    conn.commit()
    conn.close()
    return True

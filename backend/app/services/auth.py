import hashlib
import hmac
import re
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Tuple

from ..database import get_connection

from ..config import settings as _cfg
SECRET_KEY = _cfg.SECRET_KEY
SESSION_DURATION_DAYS = 30

RESERVED_USERNAMES = {
    "admin",
    "administrator",
    "support",
    "masterykeycoach",
    "mkc",
    "api",
    "system",
    "root",
    "null",
    "undefined",
    "anonymous",
    "help",
    "login",
    "register",
    "auth",
    "user",
    "users",
    "dashboard",
    "settings",
    "profile",
    "community",
}


def hash_password(password: str) -> str:
    """Generate secure PBKDF2-HMAC-SHA256 hash with 100,000 iterations and random salt."""
    salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        100000,
    )
    return f"pbkdf2_sha256$100000${salt}${key.hex()}"


def verify_password(password: str, password_hash: str) -> bool:
    """Verify password against stored PBKDF2 hash using constant-time comparison."""
    if not password or not password_hash:
        return False
    try:
        parts = password_hash.split("$")
        if len(parts) != 4 or parts[0] != "pbkdf2_sha256":
            return False
        iterations = int(parts[1])
        salt = parts[2]
        expected_key = parts[3]

        computed = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            iterations,
        )
        return hmac.compare_digest(computed.hex(), expected_key)
    except Exception:
        return False


def normalize_username(raw_username: str) -> str:
    """Strip leading @ symbol, whitespace, and convert to lowercase."""
    if not raw_username:
        return ""
    cleaned = raw_username.strip()
    if cleaned.startswith("@"):
        cleaned = cleaned[1:]
    return cleaned.lower()


def validate_username(raw_username: str) -> Tuple[bool, str]:
    """Validate username rules: 3-30 chars, [a-z0-9_], starts with letter/underscore, not reserved."""
    username = normalize_username(raw_username)
    if not username:
        return False, "Username cannot be empty."

    if len(username) < 3 or len(username) > 30:
        return False, "Username must be between 3 and 30 characters."

    if not re.match(r"^[a-z_][a-z0-9_]*$", username):
        if username[0].isdigit():
            return False, "Username cannot start with a number."
        return False, "Username can only contain letters, numbers, and underscores."

    if username in RESERVED_USERNAMES:
        return False, f"Username '{username}' is reserved by the system."

    return True, username


def is_username_available(username: str) -> bool:
    """Check if normalized username is available in database."""
    valid, normalized = validate_username(username)
    if not valid:
        return False

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE LOWER(username) = LOWER(?)", (normalized,))
    row = cursor.fetchone()
    conn.close()
    return row is None


def is_email_registered(email: str) -> bool:
    """Check if normalized email is registered in database."""
    if not email or not email.strip():
        return False
    norm_email = email.strip().lower()

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE LOWER(email) = LOWER(?)", (norm_email,))
    row = cursor.fetchone()
    conn.close()
    return row is not None


def hash_token(token: str) -> str:
    """Compute SHA-256 hash of a token for secure database storage."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_session(user_id: int, user_agent: Optional[str] = None, ip_address: Optional[str] = None) -> str:
    """Create session token and store in app_sessions DB table with device metadata."""
    token = secrets.token_urlsafe(32)
    now_dt = datetime.now(timezone.utc)
    expires_at = now_dt + timedelta(days=SESSION_DURATION_DAYS)
    now_str = now_dt.strftime("%Y-%m-%d %H:%M:%S")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO app_sessions (token, user_id, last_seen_at, user_agent, ip_address, expires_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (token, user_id, now_str, user_agent, ip_address, expires_at.strftime("%Y-%m-%d %H:%M:%S")),
    )
    conn.commit()
    conn.close()

    return token


def get_user_from_session(token: str) -> Optional[Dict[str, Any]]:
    """Retrieve user dictionary from valid session token and update last_seen_at."""
    if not token:
        return None

    conn = get_connection()
    cursor = conn.cursor()
    now_dt = datetime.now(timezone.utc)
    now_str = now_dt.strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute(
        """
        SELECT s.user_id, s.revoked_at, u.*
        FROM app_sessions s
        JOIN users u ON u.id = s.user_id
        WHERE s.token = ? AND s.expires_at > ? AND s.revoked_at IS NULL AND (u.is_active IS NULL OR u.is_active = 1)
        """,
        (token, now_str),
    )
    row = cursor.fetchone()

    if not row:
        conn.close()
        return None

    # Update last_seen_at timestamp periodically
    try:
        cursor.execute("UPDATE app_sessions SET last_seen_at = ? WHERE token = ?", (now_str, token))
        conn.commit()
    except Exception:
        pass

    conn.close()

    user_dict = dict(row)
    user_dict.pop("password_hash", None)
    user_dict.pop("revoked_at", None)
    return user_dict


def delete_session(token: str) -> None:
    """Delete session token on logout."""
    if not token:
        return
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM app_sessions WHERE token = ?", (token,))
    conn.commit()
    conn.close()


def revoke_all_sessions(user_id: int, except_token: Optional[str] = None) -> int:
    """Revoke all active sessions for a user, optionally preserving current_token."""
    conn = get_connection()
    cursor = conn.cursor()
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    if except_token:
        cursor.execute(
            """
            UPDATE app_sessions
            SET revoked_at = ?
            WHERE user_id = ? AND token != ? AND revoked_at IS NULL
            """,
            (now_str, user_id, except_token),
        )
    else:
        cursor.execute(
            """
            UPDATE app_sessions
            SET revoked_at = ?
            WHERE user_id = ? AND revoked_at IS NULL
            """,
            (now_str, user_id),
        )

    revoked_count = cursor.rowcount
    conn.commit()
    conn.close()
    return revoked_count


def list_user_sessions(user_id: int, current_token: Optional[str] = None) -> list:
    """List active sessions for user with sanitized metadata."""
    conn = get_connection()
    cursor = conn.cursor()
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute(
        """
        SELECT token, last_seen_at, created_at, user_agent, ip_address
        FROM app_sessions
        WHERE user_id = ? AND expires_at > ? AND revoked_at IS NULL
        ORDER BY last_seen_at DESC
        """,
        (user_id, now_str),
    )
    rows = cursor.fetchall()
    conn.close()

    sessions = []
    for r in rows:
        token_str = r["token"]
        # Derive device info string from user_agent
        ua = r["user_agent"] or "Unknown Device"
        browser_info = "Web Browser"
        if "Chrome" in ua:
            browser_info = "Chrome Browser"
        elif "Firefox" in ua:
            browser_info = "Firefox Browser"
        elif "Safari" in ua:
            browser_info = "Safari Browser"
        elif "Edge" in ua:
            browser_info = "Edge Browser"

        sessions.append({
            "id": token_str[:12],  # Short non-secret identifier for UI
            "device": browser_info,
            "user_agent": ua,
            "last_active": r["last_seen_at"] or r["created_at"],
            "created_at": r["created_at"],
            "is_current": token_str == current_token,
        })
    return sessions


def revoke_session_by_id(user_id: int, session_id: str) -> bool:
    """Revoke specific session by matching truncated identifier."""
    conn = get_connection()
    cursor = conn.cursor()
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute(
        """
        SELECT token FROM app_sessions
        WHERE user_id = ? AND token LIKE ? AND revoked_at IS NULL
        """,
        (user_id, f"{session_id}%"),
    )
    row = cursor.fetchone()
    if not row:
        conn.close()
        return False

    cursor.execute("UPDATE app_sessions SET revoked_at = ? WHERE token = ?", (now_str, row["token"]))
    conn.commit()
    conn.close()
    return True


def create_password_reset_token(user_id: int) -> str:
    """Create secure, random, single-use reset token (15-min expiry) and invalidate prior active tokens."""
    token = secrets.token_urlsafe(32)
    token_h = hash_token(token)
    now_dt = datetime.now(timezone.utc)
    expires_at = now_dt + timedelta(minutes=15)
    now_str = now_dt.strftime("%Y-%m-%d %H:%M:%S")

    conn = get_connection()
    cursor = conn.cursor()
    # Invalidate previous unused reset tokens for this user
    cursor.execute(
        "UPDATE password_resets SET used_at = ? WHERE user_id = ? AND used_at IS NULL",
        (now_str, user_id),
    )
    # Insert new token
    cursor.execute(
        """
        INSERT INTO password_resets (user_id, token_hash, expires_at)
        VALUES (?, ?, ?)
        """,
        (user_id, token_h, expires_at.strftime("%Y-%m-%d %H:%M:%S")),
    )
    conn.commit()
    conn.close()

    return token


def verify_and_use_reset_token(token: str, new_password: str) -> bool:
    """Verify reset token, mark as used, update password, and revoke ALL sessions for user."""
    if not token or not new_password:
        return False

    token_h = hash_token(token)
    now_dt = datetime.now(timezone.utc)
    now_str = now_dt.strftime("%Y-%m-%d %H:%M:%S")

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, user_id FROM password_resets
        WHERE token_hash = ? AND used_at IS NULL AND expires_at > ?
        """,
        (token_h, now_str),
    )
    row = cursor.fetchone()
    if not row:
        conn.close()
        return False

    reset_id = row["id"]
    user_id = row["user_id"]

    # Mark reset token as used immediately
    cursor.execute("UPDATE password_resets SET used_at = ? WHERE id = ?", (now_str, reset_id))

    # Update user password_hash
    new_pwd_hash = hash_password(new_password)
    cursor.execute("UPDATE users SET password_hash = ? WHERE id = ?", (new_pwd_hash, user_id))
    conn.commit()
    conn.close()

    # Revoke ALL existing sessions for user so other devices must log in again
    revoke_all_sessions(user_id)
    return True


def create_email_verification_token(user_id: int, email: str) -> str:
    """Create single-use email verification token (24-hr expiry)."""
    token = secrets.token_urlsafe(32)
    token_h = hash_token(token)
    now_dt = datetime.now(timezone.utc)
    expires_at = now_dt + timedelta(hours=24)
    now_str = now_dt.strftime("%Y-%m-%d %H:%M:%S")

    conn = get_connection()
    cursor = conn.cursor()
    # Invalidate previous unused verification tokens
    cursor.execute(
        "UPDATE email_verifications SET used_at = ? WHERE user_id = ? AND used_at IS NULL",
        (now_str, user_id),
    )
    cursor.execute(
        """
        INSERT INTO email_verifications (user_id, email, token_hash, expires_at)
        VALUES (?, ?, ?, ?)
        """,
        (user_id, email.strip().lower(), token_h, expires_at.strftime("%Y-%m-%d %H:%M:%S")),
    )
    conn.commit()
    conn.close()

    return token


def verify_email_token(token: str) -> bool:
    """Verify email verification token, mark as used, update user email_verified."""
    if not token:
        return False

    token_h = hash_token(token)
    now_dt = datetime.now(timezone.utc)
    now_str = now_dt.strftime("%Y-%m-%d %H:%M:%S")

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, user_id, email FROM email_verifications
        WHERE token_hash = ? AND used_at IS NULL AND expires_at > ?
        """,
        (token_h, now_str),
    )
    row = cursor.fetchone()
    if not row:
        conn.close()
        return False

    verif_id = row["id"]
    user_id = row["user_id"]

    cursor.execute("UPDATE email_verifications SET used_at = ? WHERE id = ?", (now_str, verif_id))
    cursor.execute("UPDATE users SET email_verified = 1, verified_at = ? WHERE id = ?", (now_str, user_id))
    conn.commit()
    conn.close()

    return True


def delete_user_account(user_id: int) -> None:
    """Safely delete user account and clean up all associated records and sessions."""
    conn = get_connection()
    cursor = conn.cursor()

    # Safeguard: Check if user is the last active admin
    cursor.execute("SELECT role FROM users WHERE id = ?", (user_id,))
    u_row = cursor.fetchone()
    if u_row and u_row["role"] == "admin":
        cursor.execute(
            "SELECT COUNT(*) AS admin_count FROM users WHERE role = 'admin' AND is_active = 1 AND deactivated_at IS NULL AND id != ?",
            (user_id,)
        )
        row_admin = cursor.fetchone()
        admin_count = row_admin["admin_count"] if row_admin else 0
        if admin_count == 0:
            conn.close()
            raise ValueError("Cannot delete account: You are the sole active administrator. Please designate another administrator before deleting this account.")

    # 1. Revoke sessions & tokens
    cursor.execute("DELETE FROM app_sessions WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM password_resets WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM email_verifications WHERE user_id = ?", (user_id,))

    # 2. Delete user settings & preferences
    cursor.execute("DELETE FROM user_settings WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM ai_activity_logs WHERE user_id = ?", (user_id,))

    # 3. Delete AI coach messages
    cursor.execute("DELETE FROM messages WHERE user_id = ?", (user_id,))

    # 4. Delete goals, missions, habits & journal
    cursor.execute("DELETE FROM habit_logs WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM habits WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM journal_entries WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM missions WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM goals WHERE user_id = ?", (user_id,))

    # 5. Delete life blueprint data
    cursor.execute("DELETE FROM blueprint_milestones WHERE blueprint_id IN (SELECT id FROM life_blueprints WHERE user_id = ?)", (user_id,))
    cursor.execute("DELETE FROM blueprint_phases WHERE blueprint_id IN (SELECT id FROM life_blueprints WHERE user_id = ?)", (user_id,))
    cursor.execute("DELETE FROM blueprint_areas WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM life_blueprints WHERE user_id = ?", (user_id,))

    # 6. Delete social follows, connections & conversations
    cursor.execute("DELETE FROM user_follows WHERE follower_id = ? OR following_id = ?", (user_id, user_id))
    cursor.execute("DELETE FROM user_connections WHERE requester_id = ? OR recipient_id = ?", (user_id, user_id))
    cursor.execute("DELETE FROM chat_messages WHERE sender_id = ?", (user_id,))
    cursor.execute("DELETE FROM conversation_members WHERE user_id = ?", (user_id,))

    # 7. Delete community interactions & credentials
    cursor.execute("DELETE FROM community_comments WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM community_likes WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM community_posts WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM user_credentials WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM notifications WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM feedback WHERE user_id = ?", (user_id,))

    # 8. Delete user record
    cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()


import hashlib
import hmac
import re
import secrets
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Tuple

from ..database import get_connection

SECRET_KEY = "mkc_mastery_key_coach_secret_session_key_2026"
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


def create_session(user_id: int) -> str:
    """Create session token and store in app_sessions DB table."""
    token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(days=SESSION_DURATION_DAYS)

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO app_sessions (token, user_id, expires_at)
        VALUES (?, ?, ?)
        """,
        (token, user_id, expires_at.strftime("%Y-%m-%d %H:%M:%S")),
    )
    conn.commit()
    conn.close()

    return token


def get_user_from_session(token: str) -> Optional[Dict[str, Any]]:
    """Retrieve user dictionary from valid session token."""
    if not token:
        return None

    conn = get_connection()
    cursor = conn.cursor()
    now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute(
        """
        SELECT s.user_id, u.*
        FROM app_sessions s
        JOIN users u ON u.id = s.user_id
        WHERE s.token = ? AND s.expires_at > ? AND (u.is_active IS NULL OR u.is_active = 1)
        """,
        (token, now_str),
    )
    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    user_dict = dict(row)
    user_dict.pop("password_hash", None)
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

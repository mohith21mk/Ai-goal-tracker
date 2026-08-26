import os
import sys
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from app import create_app
from app.database import get_connection, init_db
from app.services.auth import create_session, hash_password

app = create_app()
client = TestClient(app)


def setup_test_user(prefix: str, role: str = "user"):
    init_db()
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM user_follows WHERE follower_id IN (SELECT id FROM users WHERE email LIKE ?) OR following_id IN (SELECT id FROM users WHERE email LIKE ?)", (f"{prefix}%", f"{prefix}%"))
    c.execute("DELETE FROM user_connections WHERE requester_id IN (SELECT id FROM users WHERE email LIKE ?) OR recipient_id IN (SELECT id FROM users WHERE email LIKE ?)", (f"{prefix}%", f"{prefix}%"))
    c.execute("DELETE FROM app_sessions WHERE user_id IN (SELECT id FROM users WHERE email LIKE ?)", (f"{prefix}%",))
    c.execute("DELETE FROM users WHERE email LIKE ?", (f"{prefix}%",))
    conn.commit()

    pwd = hash_password("Password123!")
    c.execute(
        "INSERT INTO users (email, username, password_hash, full_name, mkc_id, email_verified, onboarding_completed, avatar_initials, role, is_active) VALUES (?, ?, ?, ?, ?, 1, 1, ?, ?, 1)",
        (f"{prefix}@test.mkc", f"u_{prefix}", pwd, f"Test {prefix}", f"MKC-{prefix.upper()}", "TD", role),
    )
    uid = c.lastrowid
    conn.commit()
    conn.close()

    token = create_session(uid)
    return uid, token


def cleanup_test_user(uid: int):
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM user_follows WHERE follower_id = ? OR following_id = ?", (uid, uid))
    c.execute("DELETE FROM user_connections WHERE requester_id = ? OR recipient_id = ?", (uid, uid))
    c.execute("DELETE FROM app_sessions WHERE user_id = ?", (uid,))
    c.execute("DELETE FROM users WHERE id = ?", (uid,))
    conn.commit()
    conn.close()


def test_delete_account_valid_flow():
    uid, token = setup_test_user("del_val")
    try:
        # Invalid confirmation text should fail
        res_fail = client.request(
            "DELETE",
            "/api/users/account",
            json={"current_password": "Password123!", "confirmation_text": "delete"},
            cookies={"mkc_session": token}
        )
        assert res_fail.status_code == 400

        # Invalid password should fail
        res_fail_pwd = client.request(
            "DELETE",
            "/api/users/account",
            json={"current_password": "WrongPassword", "confirmation_text": "DELETE MY ACCOUNT"},
            cookies={"mkc_session": token}
        )
        assert res_fail_pwd.status_code == 400

        # Valid deletion
        res_ok = client.request(
            "DELETE",
            "/api/users/account",
            json={"current_password": "Password123!", "confirmation_text": "DELETE MY ACCOUNT"},
            cookies={"mkc_session": token}
        )
        assert res_ok.status_code == 200

        # Verify user is gone from DB
        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT id FROM users WHERE id = ?", (uid,))
        assert c.fetchone() is None
        conn.close()
    finally:
        cleanup_test_user(uid)

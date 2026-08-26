import os
import sys
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from app import create_app
from app.database import get_connection, init_db
from app.services.auth import create_session, hash_password
from app.api.auth import COOKIE_NAME

app = create_app()
client = TestClient(app)


def setup_security_user(prefix: str, role: str = "user"):
    init_db()
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM user_follows WHERE follower_id IN (SELECT id FROM users WHERE email LIKE ?) OR following_id IN (SELECT id FROM users WHERE email LIKE ?)", (f"{prefix}%", f"{prefix}%"))
    c.execute("DELETE FROM user_connections WHERE requester_id IN (SELECT id FROM users WHERE email LIKE ?) OR recipient_id IN (SELECT id FROM users WHERE email LIKE ?)", (f"{prefix}%", f"{prefix}%"))
    c.execute("DELETE FROM chat_messages WHERE sender_id IN (SELECT id FROM users WHERE email LIKE ?)", (f"{prefix}%",))
    c.execute("DELETE FROM conversation_members WHERE user_id IN (SELECT id FROM users WHERE email LIKE ?)", (f"{prefix}%",))
    c.execute("DELETE FROM notifications WHERE user_id IN (SELECT id FROM users WHERE email LIKE ?)", (f"{prefix}%",))
    c.execute("DELETE FROM app_sessions WHERE user_id IN (SELECT id FROM users WHERE email LIKE ?)", (f"{prefix}%",))
    c.execute("DELETE FROM users WHERE email LIKE ?", (f"{prefix}%",))
    conn.commit()
    
    pwd = hash_password("TestPass123!")
    c.execute(
        "INSERT INTO users (email, username, password_hash, full_name, mkc_id, email_verified, onboarding_completed, avatar_initials, role) VALUES (?, ?, ?, ?, ?, 1, 1, ?, ?)",
        (f"{prefix}@sec.test", f"u_{prefix}", pwd, f"Test {prefix}", f"MKC-{prefix.upper()}", "TU", role),
    )
    uid = c.lastrowid
    conn.commit()
    conn.close()
    token = create_session(uid)
    return uid, token


def test_unauthorized_conversation_creation_rejected():
    uid_a, token_a = setup_security_user("sec_a")
    uid_b, _ = setup_security_user("sec_b")
    
    client.cookies.set(COOKIE_NAME, token_a)
    res = client.post("/api/chat/conversations", json={"target_user_id": uid_b})
    assert res.status_code in (400, 403)
    assert "connect" in res.json()["detail"].lower()


def test_upload_validation_rejects_malicious_and_oversized_files():
    uid_a, token_a = setup_security_user("sec_upload")
    client.cookies.set(COOKIE_NAME, token_a)
    
    # 1. Reject invalid file extension / MIME
    res_exe = client.post(
        "/api/chat/upload",
        files={"file": ("malware.exe", b"MZ\x90\x00\x03\x00\x00\x00", "application/x-msdownload")}
    )
    assert res_exe.status_code == 400
    assert "unsupported" in res_exe.json()["detail"].lower()
    
    # 2. Reject empty file
    res_empty = client.post(
        "/api/chat/upload",
        files={"file": ("empty.png", b"", "image/png")}
    )
    assert res_empty.status_code == 400
    
    # 3. Reject oversized image (> 5MB)
    oversized_bytes = b"\x89PNG\r\n\x1a\n" + (b"0" * (6 * 1024 * 1024))
    res_large = client.post(
        "/api/chat/upload",
        files={"file": ("large.png", oversized_bytes, "image/png")}
    )
    assert res_large.status_code == 400
    assert "exceeds" in res_large.json()["detail"].lower() or "too large" in res_large.json()["detail"].lower()


def test_account_deletion_security_guards():
    uid_a, token_a = setup_security_user("sec_del")
    client.cookies.set(COOKIE_NAME, token_a)
    
    # 1. Reject wrong confirmation phrase
    res_wrong_phrase = client.request(
        "DELETE",
        "/api/users/account",
        json={"current_password": "TestPass123!", "confirmation_text": "delete my account"}
    )
    assert res_wrong_phrase.status_code == 400
    assert "mismatch" in res_wrong_phrase.json()["detail"].lower()
    
    # 2. Reject wrong password
    res_wrong_pw = client.request(
        "DELETE",
        "/api/users/account",
        json={"current_password": "WrongPassword999!", "confirmation_text": "DELETE MY ACCOUNT"}
    )
    assert res_wrong_pw.status_code == 400
    assert "password" in res_wrong_pw.json()["detail"].lower()

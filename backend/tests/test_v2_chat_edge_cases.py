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
    c.execute("DELETE FROM user_connections WHERE requester_id IN (SELECT id FROM users WHERE email LIKE ?) OR recipient_id IN (SELECT id FROM users WHERE email LIKE ?)", (f"{prefix}%", f"{prefix}%"))
    c.execute("DELETE FROM chat_messages WHERE sender_id IN (SELECT id FROM users WHERE email LIKE ?)", (f"{prefix}%",))
    c.execute("DELETE FROM conversation_members WHERE user_id IN (SELECT id FROM users WHERE email LIKE ?)", (f"{prefix}%",))
    c.execute("DELETE FROM app_sessions WHERE user_id IN (SELECT id FROM users WHERE email LIKE ?)", (f"{prefix}%",))
    c.execute("DELETE FROM users WHERE email LIKE ?", (f"{prefix}%",))
    conn.commit()
    pwd = hash_password("TestPass123!")
    c.execute(
        "INSERT INTO users (email, username, password_hash, full_name, mkc_id, email_verified, onboarding_completed, avatar_initials) VALUES (?, ?, ?, ?, ?, 1, 1, ?)",
        (f"{prefix}@test.mkc", f"u_{prefix}", pwd, f"Test {prefix}", f"MKC-{prefix.upper()}", "TU"),
    )
    uid = c.lastrowid
    conn.commit()
    conn.close()
    token = create_session(uid)
    return uid, token


def cleanup_test_user(uid: int):
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM user_connections WHERE requester_id = ? OR recipient_id = ?", (uid, uid))
    c.execute("DELETE FROM chat_messages WHERE sender_id = ?", (uid,))
    c.execute("DELETE FROM conversation_members WHERE user_id = ?", (uid,))
    c.execute("DELETE FROM app_sessions WHERE user_id = ?", (uid,))
    c.execute("DELETE FROM users WHERE id = ?", (uid,))
    conn.commit()
    conn.close()


def test_create_conversation_unconnected_user_rejected():
    uid_a, token_a = setup_test_user("v2chat_ua")
    uid_b, token_b = setup_test_user("v2chat_ub")
    try:
        res = client.post(
            "/api/chat/conversations",
            json={"target_user_id": uid_b},
            cookies={"mkc_session": token_a},
        )
        assert res.status_code == 403, f"Expected 403 for unconnected users, got {res.status_code}"
    finally:
        cleanup_test_user(uid_a)
        cleanup_test_user(uid_b)


def test_create_conversation_with_self_rejected():
    uid, token = setup_test_user("v2chat_self")
    try:
        res = client.post(
            "/api/chat/conversations",
            json={"target_user_id": uid},
            cookies={"mkc_session": token},
        )
        assert res.status_code == 400, f"Expected 400 for self-conversation, got {res.status_code}"
    finally:
        cleanup_test_user(uid)


def test_create_conversation_missing_target_rejected():
    uid, token = setup_test_user("v2chat_notgt")
    try:
        res = client.post(
            "/api/chat/conversations",
            json={},
            cookies={"mkc_session": token},
        )
        assert res.status_code == 400, f"Expected 400 for missing target_user_id, got {res.status_code}"
    finally:
        cleanup_test_user(uid)


def test_create_conversation_nonexistent_target_rejected():
    uid, token = setup_test_user("v2chat_nonex")
    try:
        res = client.post(
            "/api/chat/conversations",
            json={"target_user_id": 9999999},
            cookies={"mkc_session": token},
        )
        assert res.status_code in (403, 404), f"Expected 403/404 for nonexistent target, got {res.status_code}"
    finally:
        cleanup_test_user(uid)


def test_conversation_lifecycle_and_reuse():
    uid_a, token_a = setup_test_user("v2chat_ca")
    uid_b, token_b = setup_test_user("v2chat_cb")
    try:
        # Establish connection via API
        client.post("/api/social/connections/request", json={"user_id": uid_b}, cookies={"mkc_session": token_a})
        client.post("/api/social/connections/accept", json={"user_id": uid_a}, cookies={"mkc_session": token_b})

        # Create conversation
        res1 = client.post(
            "/api/chat/conversations",
            json={"target_user_id": uid_b},
            cookies={"mkc_session": token_a},
        )
        assert res1.status_code == 200
        conv_id = res1.json()["id"]

        # Call again — should reuse conversation
        res2 = client.post(
            "/api/chat/conversations",
            json={"target_user_id": uid_b},
            cookies={"mkc_session": token_a},
        )
        assert res2.status_code == 200
        assert res2.json()["id"] == conv_id
        assert res2.json()["is_new"] is False

        # List conversations for both users
        res_list_a = client.get("/api/chat/conversations", cookies={"mkc_session": token_a})
        assert res_list_a.status_code == 200

        res_list_b = client.get("/api/chat/conversations", cookies={"mkc_session": token_b})
        assert res_list_b.status_code == 200
    finally:
        cleanup_test_user(uid_a)
        cleanup_test_user(uid_b)


def test_get_messages_unauthorized_member_rejected():
    uid_a, token_a = setup_test_user("v2chat_ma")
    uid_b, token_b = setup_test_user("v2chat_mb")
    uid_c, token_c = setup_test_user("v2chat_mc")
    try:
        client.post("/api/social/connections/request", json={"user_id": uid_b}, cookies={"mkc_session": token_a})
        client.post("/api/social/connections/accept", json={"user_id": uid_a}, cookies={"mkc_session": token_b})

        res_conv = client.post(
            "/api/chat/conversations",
            json={"target_user_id": uid_b},
            cookies={"mkc_session": token_a},
        )
        conv_id = res_conv.json()["id"]

        # User C tries to read messages
        res_read = client.get(
            f"/api/chat/conversations/{conv_id}/messages",
            cookies={"mkc_session": token_c},
        )
        assert res_read.status_code in (403, 404), f"Expected 403/404 for non-member, got {res_read.status_code}"
    finally:
        cleanup_test_user(uid_a)
        cleanup_test_user(uid_b)
        cleanup_test_user(uid_c)


def test_chat_unauthenticated_guards():
    res_convs = client.get("/api/chat/conversations")
    assert res_convs.status_code == 401

    res_post = client.post("/api/chat/conversations", json={"target_user_id": 1})
    assert res_post.status_code == 401

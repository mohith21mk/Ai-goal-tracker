import asyncio
import os
import sys
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from app import create_app
from app.database import get_connection, init_db
from app.services.auth import create_session, hash_password
from app.services.notifications import create_notification

app = create_app()
client = TestClient(app)


def setup_test_user(prefix: str, role: str = "user"):
    init_db()
    conn = get_connection()
    c = conn.cursor()
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
    c.execute("DELETE FROM notifications WHERE user_id = ?", (uid,))
    c.execute("DELETE FROM app_sessions WHERE user_id = ?", (uid,))
    c.execute("DELETE FROM users WHERE id = ?", (uid,))
    conn.commit()
    conn.close()


def test_unread_count_accurate_after_creation_and_mark_all():
    uid, token = setup_test_user("v2notif_cnt")
    try:
        # Create 3 notifications
        asyncio.run(create_notification(uid, "system", "Title 1", "Message 1"))
        asyncio.run(create_notification(uid, "system", "Title 2", "Message 2"))
        asyncio.run(create_notification(uid, "system", "Title 3", "Message 3"))

        res_cnt = client.get("/api/notifications/unread-count", cookies={"mkc_session": token})
        assert res_cnt.status_code == 200
        assert res_cnt.json()["unread_count"] == 3

        # Mark all read
        res_read_all = client.patch("/api/notifications/read_all", cookies={"mkc_session": token})
        assert res_read_all.status_code == 200

        # Unread count should be 0
        res_cnt2 = client.get("/api/notifications/unread-count", cookies={"mkc_session": token})
        assert res_cnt2.status_code == 200
        assert res_cnt2.json()["unread_count"] == 0
    finally:
        cleanup_test_user(uid)


def test_mark_single_notification_read_and_delete():
    uid, token = setup_test_user("v2notif_sngl")
    try:
        notif = asyncio.run(create_notification(uid, "system", "Single Test", "Message single"))
        nid = notif["id"]

        # Mark read
        res_read = client.patch(f"/api/notifications/{nid}/read", cookies={"mkc_session": token})
        assert res_read.status_code == 200

        # Delete notification
        res_del = client.delete(f"/api/notifications/{nid}", cookies={"mkc_session": token})
        assert res_del.status_code == 200

        # Deleting again returns 404
        res_del2 = client.delete(f"/api/notifications/{nid}", cookies={"mkc_session": token})
        assert res_del2.status_code == 404
    finally:
        cleanup_test_user(uid)


def test_notification_cross_user_isolation():
    uid_a, token_a = setup_test_user("v2notif_ua")
    uid_b, token_b = setup_test_user("v2notif_ub")
    try:
        notif_a = asyncio.run(create_notification(uid_a, "system", "User A Secret", "Msg A"))
        nid_a = notif_a["id"]

        # User B cannot mark User A's notification as read
        res_read = client.patch(f"/api/notifications/{nid_a}/read", cookies={"mkc_session": token_b})
        assert res_read.status_code == 404

        # User B cannot delete User A's notification
        res_del = client.delete(f"/api/notifications/{nid_a}", cookies={"mkc_session": token_b})
        assert res_del.status_code == 404
    finally:
        cleanup_test_user(uid_a)
        cleanup_test_user(uid_b)


def test_notifications_unauthenticated_guards():
    res_list = client.get("/api/notifications")
    assert res_list.status_code == 401

    res_unread = client.get("/api/notifications/unread-count")
    assert res_unread.status_code == 401

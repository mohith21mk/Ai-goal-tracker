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
    c.execute("DELETE FROM chat_messages WHERE sender_id IN (SELECT id FROM users WHERE email LIKE ?)", (f"{prefix}%",))
    c.execute("DELETE FROM conversation_members WHERE user_id IN (SELECT id FROM users WHERE email LIKE ?)", (f"{prefix}%",))
    c.execute("DELETE FROM notifications WHERE user_id IN (SELECT id FROM users WHERE email LIKE ?)", (f"{prefix}%",))
    c.execute("DELETE FROM app_sessions WHERE user_id IN (SELECT id FROM users WHERE email LIKE ?)", (f"{prefix}%",))
    c.execute("DELETE FROM users WHERE email LIKE ?", (f"{prefix}%",))
    conn.commit()
    pwd = hash_password("TestPass123!")
    c.execute(
        "INSERT INTO users (email, username, password_hash, full_name, mkc_id, email_verified, onboarding_completed, avatar_initials, role) VALUES (?, ?, ?, ?, ?, 1, 1, ?, ?)",
        (f"{prefix}@test.mkc", f"u_{prefix}", pwd, f"Test {prefix}", f"MKC-{prefix.upper()}", "TU", role),
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
    c.execute("DELETE FROM chat_messages WHERE sender_id = ?", (uid,))
    c.execute("DELETE FROM conversation_members WHERE user_id = ?", (uid,))
    c.execute("DELETE FROM notifications WHERE user_id = ?", (uid,))
    c.execute("DELETE FROM app_sessions WHERE user_id = ?", (uid,))
    c.execute("DELETE FROM users WHERE id = ?", (uid,))
    conn.commit()
    conn.close()


def test_follow_and_unfollow_flow():
    uid_a, token_a = setup_test_user("fol_a")
    uid_b, token_b = setup_test_user("fol_b")

    try:
        # 1. Check initial stats (0 followers, 0 following)
        res = client.get(f"/api/social/follow-stats/{uid_b}", cookies={"mkc_session": token_a})
        assert res.status_code == 200
        stats = res.json()
        assert stats["followers_count"] == 0
        assert stats["following_count"] == 0
        assert stats["is_following"] is False

        # 2. User A follows User B
        res_follow = client.post(f"/api/social/follow/{uid_b}", cookies={"mkc_session": token_a})
        assert res_follow.status_code == 200
        assert res_follow.json()["is_following"] is True

        # 3. Check stats for User B
        res_stats_b = client.get(f"/api/social/follow-stats/{uid_b}", cookies={"mkc_session": token_a})
        assert res_stats_b.status_code == 200
        assert res_stats_b.json()["followers_count"] == 1
        assert res_stats_b.json()["is_following"] is True

        # 4. Check stats for User A (User A has 1 following)
        res_stats_a = client.get(f"/api/social/follow-stats/{uid_a}", cookies={"mkc_session": token_a})
        assert res_stats_a.status_code == 200
        assert res_stats_a.json()["following_count"] == 1

        # 5. Get User B's followers list -> User A should be listed
        res_followers = client.get(f"/api/social/followers/{uid_b}", cookies={"mkc_session": token_b})
        assert res_followers.status_code == 200
        followers_list = res_followers.json()
        assert len(followers_list) == 1
        assert followers_list[0]["id"] == uid_a

        # 6. User A unfollows User B
        res_unfollow = client.post(f"/api/social/unfollow/{uid_b}", cookies={"mkc_session": token_a})
        assert res_unfollow.status_code == 200
        assert res_unfollow.json()["is_following"] is False

        # 7. Check stats after unfollow
        res_stats_after = client.get(f"/api/social/follow-stats/{uid_b}", cookies={"mkc_session": token_a})
        assert res_stats_after.status_code == 200
        assert res_stats_after.json()["followers_count"] == 0
        assert res_stats_after.json()["is_following"] is False
    finally:
        cleanup_test_user(uid_a)
        cleanup_test_user(uid_b)


def test_cannot_follow_self():
    uid_a, token_a = setup_test_user("fol_self")
    try:
        res = client.post(f"/api/social/follow/{uid_a}", cookies={"mkc_session": token_a})
        assert res.status_code == 400
        assert "yourself" in res.json()["detail"].lower()
    finally:
        cleanup_test_user(uid_a)

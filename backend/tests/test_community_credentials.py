"""
Targeted tests for Community Victory Posts with Credential Attachment.
Verifies server-side credential ownership validation, anti-forgery, and safe rendering.
"""
import os
import sys
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.main import app
from app.database import get_connection, init_db
from app.services.auth import create_session, hash_password

client = TestClient(app)


def setup_test_users():
    init_db()
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM community_comments WHERE user_id IN (SELECT id FROM users WHERE email LIKE 'comm_test%' OR username LIKE 'comm_user_%')")
    cursor.execute("DELETE FROM community_likes WHERE user_id IN (SELECT id FROM users WHERE email LIKE 'comm_test%' OR username LIKE 'comm_user_%')")
    cursor.execute("DELETE FROM community_posts WHERE user_id IN (SELECT id FROM users WHERE email LIKE 'comm_test%' OR username LIKE 'comm_user_%')")
    cursor.execute("DELETE FROM user_credentials WHERE user_id IN (SELECT id FROM users WHERE email LIKE 'comm_test%' OR username LIKE 'comm_user_%')")
    cursor.execute("DELETE FROM app_sessions WHERE user_id IN (SELECT id FROM users WHERE email LIKE 'comm_test%' OR username LIKE 'comm_user_%')")
    cursor.execute("DELETE FROM users WHERE email LIKE 'comm_test%' OR username LIKE 'comm_user_%'")
    conn.commit()

    pwd = hash_password("Test1234!")
    
    # User A
    cursor.execute(
        "INSERT INTO users (email, full_name, username, password_hash, avatar_initials) VALUES (?, ?, ?, ?, ?)",
        ("comm_test_a@example.com", "TestUser Alpha", "comm_user_a", pwd, "UA"),
    )
    user_a_id = cursor.lastrowid

    # User B
    cursor.execute(
        "INSERT INTO users (email, full_name, username, password_hash, avatar_initials) VALUES (?, ?, ?, ?, ?)",
        ("comm_test_b@example.com", "TestUser Beta", "comm_user_b", pwd, "UB"),
    )
    user_b_id = cursor.lastrowid

    # Give User A a verified credential
    cursor.execute(
        """
        INSERT INTO user_credentials (user_id, credential_type, slug, title, description, tier, xp_value, evidence_type)
        VALUES (?, 'streak_badge', 'streak_30', '30-Day Momentum Vanguard', 'Completed 30-day streak', 'gold', 150, 'habit_streak')
        """,
        (user_a_id,),
    )
    cred_a_id = cursor.lastrowid

    conn.commit()
    conn.close()

    token_a = create_session(user_a_id)
    token_b = create_session(user_b_id)

    return (user_a_id, token_a, cred_a_id), (user_b_id, token_b)


def test_create_post_with_valid_owned_credential():
    (user_a_id, token_a, cred_a_id), (user_b_id, token_b) = setup_test_users()
    cookies_a = {"mkc_session": token_a}

    res = client.post(
        "/api/community/posts",
        json={
            "content": "I achieved a 30-day momentum streak!",
            "category": "wins",
            "credential_id": cred_a_id,
        },
        cookies=cookies_a,
    )
    assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
    data = res.json()
    assert data["credential_id"] == cred_a_id
    assert data["credential"] is not None
    assert data["credential"]["title"] == "30-Day Momentum Vanguard"
    assert data["credential"]["tier"] == "gold"


def test_reject_post_with_unowned_credential():
    (user_a_id, token_a, cred_a_id), (user_b_id, token_b) = setup_test_users()
    cookies_b = {"mkc_session": token_b}

    # User B tries to attach User A's credential
    res = client.post(
        "/api/community/posts",
        json={
            "content": "Trying to steal User A's credential!",
            "category": "wins",
            "credential_id": cred_a_id,
        },
        cookies=cookies_b,
    )
    assert res.status_code == 400, f"Expected 400 Bad Request, got {res.status_code}"
    assert "Invalid or unauthorized" in res.json()["detail"]


def test_reject_post_with_nonexistent_credential():
    (user_a_id, token_a, cred_a_id), (user_b_id, token_b) = setup_test_users()
    cookies_a = {"mkc_session": token_a}

    res = client.post(
        "/api/community/posts",
        json={
            "content": "Fabricated credential ID",
            "category": "wins",
            "credential_id": 999999,
        },
        cookies=cookies_a,
    )
    assert res.status_code == 400


def test_list_posts_returns_attached_credential_and_backwards_compatibility():
    (user_a_id, token_a, cred_a_id), (user_b_id, token_b) = setup_test_users()
    cookies_a = {"mkc_session": token_a}

    # Post with credential
    client.post(
        "/api/community/posts",
        json={
            "content": "Victory with credential",
            "category": "wins",
            "credential_id": cred_a_id,
        },
        cookies=cookies_a,
    )

    # Post without credential
    client.post(
        "/api/community/posts",
        json={
            "content": "Normal mindset post",
            "category": "mindset",
        },
        cookies=cookies_a,
    )

    res = client.get("/api/community/posts", cookies=cookies_a)
    assert res.status_code == 200
    posts = res.json()
    assert len(posts) >= 2
    
    cred_post = next((p for p in posts if p["content"] == "Victory with credential"), None)
    assert cred_post is not None
    assert cred_post["credential"] is not None
    assert cred_post["credential"]["tier"] == "gold"

    normal_post = next((p for p in posts if p["content"] == "Normal mindset post"), None)
    assert normal_post is not None
    assert normal_post["credential"] is None


if __name__ == "__main__":
    print("Running community credentials tests...")
    test_create_post_with_valid_owned_credential()
    print("[PASS] test_create_post_with_valid_owned_credential passed")
    test_reject_post_with_unowned_credential()
    print("[PASS] test_reject_post_with_unowned_credential passed")
    test_reject_post_with_nonexistent_credential()
    print("[PASS] test_reject_post_with_nonexistent_credential passed")
    test_list_posts_returns_attached_credential_and_backwards_compatibility()
    print("[PASS] test_list_posts_returns_attached_credential_and_backwards_compatibility passed")
    print("ALL COMMUNITY CREDENTIAL TESTS PASSED!")

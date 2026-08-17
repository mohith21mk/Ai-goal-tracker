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
    c.execute("DELETE FROM community_comments WHERE user_id = ?", (uid,))
    c.execute("DELETE FROM community_likes WHERE user_id = ?", (uid,))
    c.execute("DELETE FROM community_posts WHERE user_id = ?", (uid,))
    c.execute("DELETE FROM app_sessions WHERE user_id = ?", (uid,))
    c.execute("DELETE FROM users WHERE id = ?", (uid,))
    conn.commit()
    conn.close()


def test_create_post_empty_content_rejected():
    uid, token = setup_test_user("v2comm_emp")
    try:
        res = client.post(
            "/api/community/posts",
            json={"content": "   ", "category": "general"},
            cookies={"mkc_session": token},
        )
        assert res.status_code == 422, f"Expected 422 for empty content, got {res.status_code}"
    finally:
        cleanup_test_user(uid)


def test_create_post_invalid_category_rejected():
    uid, token = setup_test_user("v2comm_cat")
    try:
        res = client.post(
            "/api/community/posts",
            json={"content": "Valid post content", "category": "invalid_category"},
            cookies={"mkc_session": token},
        )
        assert res.status_code == 422, f"Expected 422 for invalid category, got {res.status_code}"
    finally:
        cleanup_test_user(uid)


def test_create_post_oversized_content_rejected():
    uid, token = setup_test_user("v2comm_over")
    try:
        res = client.post(
            "/api/community/posts",
            json={"content": "x" * 1001, "category": "general"},
            cookies={"mkc_session": token},
        )
        assert res.status_code == 422, f"Expected 422 for oversized content, got {res.status_code}"
    finally:
        cleanup_test_user(uid)


def test_update_post_not_author_rejected():
    uid_a, token_a = setup_test_user("v2comm_ua")
    uid_b, token_b = setup_test_user("v2comm_ub")
    try:
        res = client.post(
            "/api/community/posts",
            json={"content": "Author A Post", "category": "wins"},
            cookies={"mkc_session": token_a},
        )
        assert res.status_code in (200, 201)
        post_id = res.json()["id"]

        # User B tries to update User A's post
        res_update = client.patch(
            f"/api/community/posts/{post_id}",
            json={"content": "Hacked content"},
            cookies={"mkc_session": token_b},
        )
        assert res_update.status_code in (403, 404), f"Expected 403 or 404, got {res_update.status_code}"
    finally:
        cleanup_test_user(uid_a)
        cleanup_test_user(uid_b)


def test_delete_post_not_author_rejected():
    uid_a, token_a = setup_test_user("v2comm_da")
    uid_b, token_b = setup_test_user("v2comm_db")
    try:
        res = client.post(
            "/api/community/posts",
            json={"content": "Author A Post to Delete", "category": "mindset"},
            cookies={"mkc_session": token_a},
        )
        assert res.status_code in (200, 201)
        post_id = res.json()["id"]

        # User B tries to delete User A's post
        res_del = client.delete(
            f"/api/community/posts/{post_id}",
            cookies={"mkc_session": token_b},
        )
        assert res_del.status_code in (403, 404), f"Expected 403 or 404, got {res_del.status_code}"
    finally:
        cleanup_test_user(uid_a)
        cleanup_test_user(uid_b)


def test_like_and_unlike_post_lifecycle():
    uid, token = setup_test_user("v2comm_like")
    try:
        res = client.post(
            "/api/community/posts",
            json={"content": "Post to like", "category": "general"},
            cookies={"mkc_session": token},
        )
        post_id = res.json()["id"]

        # Toggle like on
        res_like = client.post(f"/api/community/posts/{post_id}/like", cookies={"mkc_session": token})
        assert res_like.status_code == 200

        # Explicit delete like
        res_unlike = client.delete(f"/api/community/posts/{post_id}/like", cookies={"mkc_session": token})
        assert res_unlike.status_code == 200
    finally:
        cleanup_test_user(uid)


def test_comment_empty_content_rejected():
    uid, token = setup_test_user("v2comm_cmte")
    try:
        res = client.post(
            "/api/community/posts",
            json={"content": "Post for comment", "category": "general"},
            cookies={"mkc_session": token},
        )
        post_id = res.json()["id"]

        res_cmt = client.post(
            f"/api/community/posts/{post_id}/comments",
            json={"content": "   "},
            cookies={"mkc_session": token},
        )
        assert res_cmt.status_code == 422, f"Expected 422, got {res_cmt.status_code}"
    finally:
        cleanup_test_user(uid)


def test_comment_update_and_delete_permissions():
    uid_a, token_a = setup_test_user("v2comm_ca")
    uid_b, token_b = setup_test_user("v2comm_cb")
    try:
        res = client.post(
            "/api/community/posts",
            json={"content": "Post for comments test", "category": "questions"},
            cookies={"mkc_session": token_a},
        )
        post_id = res.json()["id"]

        # User A adds comment
        res_cmt = client.post(
            f"/api/community/posts/{post_id}/comments",
            json={"content": "Comment by Author A"},
            cookies={"mkc_session": token_a},
        )
        assert res_cmt.status_code in (200, 201)
        comment_id = res_cmt.json()["id"]

        # User B tries to update User A's comment
        res_upd = client.patch(
            f"/api/community/comments/{comment_id}",
            json={"content": "Hacked comment"},
            cookies={"mkc_session": token_b},
        )
        assert res_upd.status_code in (403, 404), f"Expected 403/404, got {res_upd.status_code}"

        # User B tries to delete User A's comment
        res_del = client.delete(
            f"/api/community/comments/{comment_id}",
            cookies={"mkc_session": token_b},
        )
        assert res_del.status_code in (403, 404), f"Expected 403/404, got {res_del.status_code}"

        # User A successfully updates comment
        res_owner_upd = client.patch(
            f"/api/community/comments/{comment_id}",
            json={"content": "Updated comment by Author A"},
            cookies={"mkc_session": token_a},
        )
        assert res_owner_upd.status_code == 200

        # User A successfully deletes comment
        res_owner_del = client.delete(
            f"/api/community/comments/{comment_id}",
            cookies={"mkc_session": token_a},
        )
        assert res_owner_del.status_code == 200
    finally:
        cleanup_test_user(uid_a)
        cleanup_test_user(uid_b)


def test_community_unauthenticated_guards():
    res_feed = client.get("/api/community/posts")
    assert res_feed.status_code == 401

    res_post = client.post("/api/community/posts", json={"content": "No auth"})
    assert res_post.status_code == 401

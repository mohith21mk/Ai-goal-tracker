import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import init_db, get_connection

client = TestClient(app)

def setup_module(module):
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM community_comments WHERE user_id IN (SELECT id FROM users WHERE username IN ('comm_user_a', 'comm_user_b') OR email IN ('comma@example.com', 'commb@example.com'))")
    cursor.execute("DELETE FROM community_likes WHERE user_id IN (SELECT id FROM users WHERE username IN ('comm_user_a', 'comm_user_b') OR email IN ('comma@example.com', 'commb@example.com'))")
    cursor.execute("DELETE FROM community_posts WHERE user_id IN (SELECT id FROM users WHERE username IN ('comm_user_a', 'comm_user_b') OR email IN ('comma@example.com', 'commb@example.com'))")
    cursor.execute("DELETE FROM app_sessions WHERE user_id IN (SELECT id FROM users WHERE username IN ('comm_user_a', 'comm_user_b') OR email IN ('comma@example.com', 'commb@example.com'))")
    cursor.execute("DELETE FROM users WHERE username IN ('comm_user_a', 'comm_user_b') OR email IN ('comma@example.com', 'commb@example.com')")
    conn.commit()
    conn.close()

def test_phase2f_community_social_suite():
    # 1. Unauthenticated Request Check
    unauth = client.get("/api/community/posts")
    assert unauth.status_code == 401

    # Register User A & User B
    res_a = client.post("/api/auth/register", json={
        "email": "comma@example.com", "password": "Password123!", "full_name": "Comm User A", "username": "comm_user_a"
    })
    assert res_a.status_code == 200
    token_a = res_a.cookies.get("mkc_session") or res_a.json().get("session_token")
    headers_a = {"Cookie": f"mkc_session={token_a}"}
    user_a_id = res_a.json().get("id") or res_a.json().get("user_id")

    res_b = client.post("/api/auth/register", json={
        "email": "commb@example.com", "password": "Password123!", "full_name": "Comm User B", "username": "comm_user_b"
    })
    assert res_b.status_code == 200
    token_b = res_b.cookies.get("mkc_session") or res_b.json().get("session_token")
    headers_b = {"Cookie": f"mkc_session={token_b}"}

    # 2. Empty Post Rejection
    empty_post = client.post("/api/community/posts", json={"content": "   ", "category": "general"}, headers=headers_a)
    assert empty_post.status_code in (400, 422)

    # 3. Create Valid Post (User A)
    post_res = client.post("/api/community/posts", json={
        "content": "Starting my deep work challenge today.",
        "category": "wins"
    }, headers=headers_a)
    assert post_res.status_code == 200
    post = post_res.json()
    post_id = post["id"]
    assert post["content"] == "Starting my deep work challenge today."
    assert post["category"] == "wins"

    # 4. Single Post Retrieval & 404 Check
    single_res = client.get(f"/api/community/posts/{post_id}", headers=headers_b)
    assert single_res.status_code == 200
    assert single_res.json()["id"] == post_id

    missing_res = client.get("/api/community/posts/99999", headers=headers_b)
    assert missing_res.status_code == 404

    # 5. Feed Retrieval & Category Filtering (User B views feed)
    feed_res = client.get("/api/community/posts?category=wins", headers=headers_b)
    assert feed_res.status_code == 200
    posts = feed_res.json()
    assert any(p["id"] == post_id for p in posts)

    # 6. Unauthorized Post Edit Attempt (User B tries to edit User A's post)
    unauth_edit = client.patch(f"/api/community/posts/{post_id}", json={"content": "Hacked content"}, headers=headers_b)
    assert unauth_edit.status_code == 403

    # 7. Post Edit by Owner (User A)
    owner_edit = client.patch(f"/api/community/posts/{post_id}", json={"content": "Starting my deep work challenge today. Phase 1 active!"}, headers=headers_a)
    assert owner_edit.status_code == 200
    assert owner_edit.json()["content"] == "Starting my deep work challenge today. Phase 1 active!"

    # 8. Like Post & Duplicate Like Prevention (User B likes User A's post)
    like_res1 = client.post(f"/api/community/posts/{post_id}/like", headers=headers_b)
    assert like_res1.status_code == 200
    assert like_res1.json()["likes_count"] == 1
    assert like_res1.json()["user_has_liked"] is True

    # Toggle again -> unlikes
    like_res2 = client.post(f"/api/community/posts/{post_id}/like", headers=headers_b)
    assert like_res2.status_code == 200
    assert like_res2.json()["likes_count"] == 0
    assert like_res2.json()["user_has_liked"] is False

    # Like again for explicit unlike test
    client.post(f"/api/community/posts/{post_id}/like", headers=headers_b)
    explicit_unlike = client.delete(f"/api/community/posts/{post_id}/like", headers=headers_b)
    assert explicit_unlike.status_code == 200
    assert explicit_unlike.json()["likes_count"] == 0

    # User B likes again to trigger notification for User A
    client.post(f"/api/community/posts/{post_id}/like", headers=headers_b)

    # 9. Verify Notification Generation for User A
    notifs_a = client.get("/api/notifications", headers=headers_a).json()
    assert any(n["type"] == "community_like" and n["reference_id"] == post_id for n in notifs_a)

    # 10. Comment Creation & Rejection (User B comments on User A's post)
    empty_comm = client.post(f"/api/community/posts/{post_id}/comments", json={"content": ""}, headers=headers_b)
    assert empty_comm.status_code in (400, 422)

    comm_res = client.post(f"/api/community/posts/{post_id}/comments", json={"content": "Let's do it!"}, headers=headers_b)
    assert comm_res.status_code == 200
    comment = comm_res.json()
    comment_id = comment["id"]
    assert comment["content"] == "Let's do it!"

    # 11. Comment Retrieval
    comms_list = client.get(f"/api/community/posts/{post_id}/comments", headers=headers_a).json()
    assert any(c["id"] == comment_id for c in comms_list)

    # 12. Unauthorized Comment Edit & Delete (User A tries to edit/delete User B's comment)
    unauth_comm_edit = client.patch(f"/api/community/comments/{comment_id}", json={"content": "Altered comment"}, headers=headers_a)
    assert unauth_comm_edit.status_code == 403

    unauth_comm_del = client.delete(f"/api/community/comments/{comment_id}", headers=headers_a)
    assert unauth_comm_del.status_code == 403

    # 13. Comment Edit & Delete by Owner (User B)
    owner_comm_edit = client.patch(f"/api/community/comments/{comment_id}", json={"content": "Let's do it together!"}, headers=headers_b)
    assert owner_comm_edit.status_code == 200
    assert owner_comm_edit.json()["content"] == "Let's do it together!"

    owner_comm_del = client.delete(f"/api/community/comments/{comment_id}", headers=headers_b)
    assert owner_comm_del.status_code == 200

    # 14. Unauthorized Post Deletion (User B tries to delete User A's post)
    unauth_del = client.delete(f"/api/community/posts/{post_id}", headers=headers_b)
    assert unauth_del.status_code == 403

    # 15. Post Deletion by Owner (User A)
    owner_del = client.delete(f"/api/community/posts/{post_id}", headers=headers_a)
    assert owner_del.status_code == 200

    print("Phase 2F Community & Social Test Suite PASSED 100%.")

def teardown_module(module):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE username IN ('comm_user_a', 'comm_user_b')")
    conn.commit()
    conn.close()

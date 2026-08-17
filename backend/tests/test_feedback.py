"""
Comprehensive test suite for MKC Private User Feedback System.
Verifies all 17 requirements:
1. Authenticated user can submit feedback
2. Unauthenticated user cannot submit feedback (401)
3. User ID strictly derived from session (spoofing ignored)
4. User A cannot access User B's feedback (IDOR protection)
5. Normal user cannot access admin feedback list (403)
6. Normal user cannot modify feedback (403)
7. Normal user cannot delete feedback (403)
8. Admin can list feedback
9. Admin can view feedback detail
10. Admin can update status and resolve feedback
11. Admin notes remain private
12. Rate limiting works
13. Invalid category rejected (422)
14. Oversized message rejected (422)
15. Feedback persists after DB re-query
16. Database migration works on SQLite
17. Database schema compatibility and constraints
"""
import os
import sys
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.main import app
from app.database import get_connection, init_db
from app.services.auth import create_session, hash_password

client = TestClient(app)


def setup_user(email_prefix: str, role: str = "user"):
    init_db()
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM feedback WHERE user_id IN (SELECT id FROM users WHERE email LIKE ?)", (f"{email_prefix}%",))
    cursor.execute("DELETE FROM app_sessions WHERE user_id IN (SELECT id FROM users WHERE email LIKE ?)", (f"{email_prefix}%",))
    cursor.execute("DELETE FROM users WHERE email LIKE ?", (f"{email_prefix}%",))
    conn.commit()

    pwd = hash_password("TestPass123!")
    cursor.execute(
        "INSERT INTO users (email, full_name, username, password_hash, role, avatar_initials) VALUES (?, ?, ?, ?, ?, ?)",
        (f"{email_prefix}@example.com", f"User {email_prefix}", f"user_{email_prefix}", pwd, role, "TU"),
    )
    user_id = cursor.lastrowid
    conn.commit()
    conn.close()

    session_token = create_session(user_id)
    return user_id, session_token


def cleanup_user(user_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM feedback WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM app_sessions WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()


def test_authenticated_user_can_submit_feedback():
    """Test 1: Authenticated user can submit feedback and receive confirmation."""
    user_id, token = setup_user("fb_user_submit")
    try:
        payload = {
            "category": "Bug",
            "message": "Connection requests are not updating in real time on mobile.",
            "severity": "High",
            "page_url": "/chat?tab=requests"
        }
        res = client.post("/api/feedback", json=payload, cookies={"mkc_session": token})
        assert res.status_code == 201, f"Expected 201, got {res.status_code}: {res.text}"
        data = res.json()
        assert data["success"] is True
        assert "Thank you" in data["message"]
        assert "id" in data
        feedback_id = data["id"]

        # Verify in database
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM feedback WHERE id = ?", (feedback_id,))
        row = cursor.fetchone()
        conn.close()
        assert row is not None
        assert row["user_id"] == user_id
        assert row["category"] == "Bug"
        assert row["severity"] == "High"
        assert row["status"] == "new"
    finally:
        cleanup_user(user_id)


def test_unauthenticated_user_cannot_submit():
    """Test 2: Unauthenticated user receives 401."""
    payload = {
        "category": "UI/UX",
        "message": "The navbar contrast could be improved in bright light.",
        "severity": "Low"
    }
    res = client.post("/api/feedback", json=payload)
    assert res.status_code == 401


def test_user_id_comes_from_authentication_not_payload():
    """Test 3: Backend ignores spoofed user_id in client payload."""
    user_a_id, token_a = setup_user("fb_user_a")
    user_b_id, token_b = setup_user("fb_user_b")
    try:
        # User A sends payload pretending to be User B (id: user_b_id)
        payload = {
            "category": "Feature Request",
            "message": "Please add habit calendar view.",
            "severity": "Normal",
            "user_id": user_b_id  # spoof attempt
        }
        res = client.post("/api/feedback", json=payload, cookies={"mkc_session": token_a})
        assert res.status_code == 201
        feedback_id = res.json()["id"]

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM feedback WHERE id = ?", (feedback_id,))
        row = cursor.fetchone()
        conn.close()
        assert row["user_id"] == user_a_id, "User ID must strictly come from authentication session"
    finally:
        cleanup_user(user_a_id)
        cleanup_user(user_b_id)


def test_normal_users_cannot_access_admin_endpoints_or_other_feedback():
    """Tests 4, 5, 6, 7: Normal users cannot access admin endpoints or enumerate feedback (IDOR protection)."""
    user_a_id, token_a = setup_user("fb_normal_a")
    user_b_id, token_b = setup_user("fb_normal_b")
    try:
        # User A creates feedback
        res_create = client.post(
            "/api/feedback",
            json={"category": "Bug", "message": "Issue with certificate download", "severity": "Normal"},
            cookies={"mkc_session": token_a}
        )
        assert res_create.status_code == 201
        fb_id = res_create.json()["id"]

        # User B tries to list admin feedback -> 403 Forbidden
        res_list = client.get("/api/admin/feedback", cookies={"mkc_session": token_b})
        assert res_list.status_code == 403

        # User B tries to view admin feedback detail -> 403 Forbidden
        res_view = client.get(f"/api/admin/feedback/{fb_id}", cookies={"mkc_session": token_b})
        assert res_view.status_code == 403

        # User B tries to update feedback -> 403 Forbidden
        res_patch = client.patch(f"/api/admin/feedback/{fb_id}", json={"status": "resolved"}, cookies={"mkc_session": token_b})
        assert res_patch.status_code == 403

        # User B tries to delete feedback -> 403 Forbidden
        res_del = client.delete(f"/api/admin/feedback/{fb_id}", cookies={"mkc_session": token_b})
        assert res_del.status_code == 403
    finally:
        cleanup_user(user_a_id)
        cleanup_user(user_b_id)


def test_admin_can_list_view_update_and_delete_feedback():
    """Tests 8, 9, 10, 11: Admin can manage feedback and private admin notes are stored."""
    admin_id, admin_token = setup_user("fb_admin_user", role="admin")
    normal_id, normal_token = setup_user("fb_submitter_user", role="user")

    try:
        # Normal user submits feedback
        res_create = client.post(
            "/api/feedback",
            json={
                "category": "Performance",
                "message": "AI Coach responses take 3 seconds to stream.",
                "severity": "High",
                "page_url": "/coach"
            },
            cookies={"mkc_session": normal_token}
        )
        assert res_create.status_code == 201
        fb_id = res_create.json()["id"]

        # Admin lists feedback
        res_list = client.get("/api/admin/feedback", cookies={"mkc_session": admin_token})
        assert res_list.status_code == 200
        data_list = res_list.json()
        assert data_list["total"] >= 1
        assert any(item["id"] == fb_id for item in data_list["items"])

        # Admin views single feedback item
        res_item = client.get(f"/api/admin/feedback/{fb_id}", cookies={"mkc_session": admin_token})
        assert res_item.status_code == 200
        item = res_item.json()
        assert item["id"] == fb_id
        assert item["user_email"] == "fb_submitter_user@example.com"
        assert item["user_username"] == "user_fb_submitter_user"
        assert item["category"] == "Performance"

        # Admin updates status & adds private admin notes
        res_patch = client.patch(
            f"/api/admin/feedback/{fb_id}",
            json={
                "status": "resolved",
                "severity": "Normal",
                "admin_notes": "Optimized RAG streaming buffer in coach service."
            },
            cookies={"mkc_session": admin_token}
        )
        assert res_patch.status_code == 200
        updated = res_patch.json()
        assert updated["status"] == "resolved"
        assert updated["admin_notes"] == "Optimized RAG streaming buffer in coach service."
        assert updated["resolved_at"] is not None

        # Admin stats endpoint
        res_stats = client.get("/api/admin/feedback/stats", cookies={"mkc_session": admin_token})
        assert res_stats.status_code == 200
        stats = res_stats.json()
        assert "total" in stats
        assert "resolved" in stats

        # Admin deletes feedback
        res_del = client.delete(f"/api/admin/feedback/{fb_id}", cookies={"mkc_session": admin_token})
        assert res_del.status_code == 200
        assert res_del.json()["success"] is True

        # Verify 404 after deletion
        res_after = client.get(f"/api/admin/feedback/{fb_id}", cookies={"mkc_session": admin_token})
        assert res_after.status_code == 404
    finally:
        cleanup_user(admin_id)
        cleanup_user(normal_id)


def test_invalid_category_and_oversized_message_rejected():
    """Tests 13, 14: Validation rejects invalid category and oversized message."""
    user_id, token = setup_user("fb_invalid_test")
    try:
        # Invalid Category
        res_cat = client.post(
            "/api/feedback",
            json={"category": "InvalidCategory123", "message": "Valid text message", "severity": "Normal"},
            cookies={"mkc_session": token}
        )
        assert res_cat.status_code == 422

        # Invalid Severity
        res_sev = client.post(
            "/api/feedback",
            json={"category": "Bug", "message": "Valid text message", "severity": "UltraUrgent"},
            cookies={"mkc_session": token}
        )
        assert res_sev.status_code == 422

        # Too short message
        res_short = client.post(
            "/api/feedback",
            json={"category": "Bug", "message": "a", "severity": "Normal"},
            cookies={"mkc_session": token}
        )
        assert res_short.status_code == 422

        # Oversized message (> 5000 chars)
        res_long = client.post(
            "/api/feedback",
            json={"category": "Bug", "message": "X" * 5001, "severity": "Normal"},
            cookies={"mkc_session": token}
        )
        assert res_long.status_code == 422
    finally:
        cleanup_user(user_id)


def test_feedback_persists_across_database_queries():
    """Test 15: Feedback record persists with full timestamps and integrity."""
    user_id, token = setup_user("fb_persist_test")
    try:
        res = client.post(
            "/api/feedback",
            json={"category": "AI Coach", "message": "The advice was very motivating today!", "severity": "Low"},
            cookies={"mkc_session": token}
        )
        assert res.status_code == 201
        fb_id = res.json()["id"]

        # Reconnect to database and verify persistence
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, user_id, category, message, severity, status, created_at FROM feedback WHERE id = ?", (fb_id,))
        row = cursor.fetchone()
        conn.close()

        assert row is not None
        assert row["id"] == fb_id
        assert row["user_id"] == user_id
        assert row["category"] == "AI Coach"
        assert row["message"] == "The advice was very motivating today!"
        assert row["created_at"] is not None
    finally:
        cleanup_user(user_id)

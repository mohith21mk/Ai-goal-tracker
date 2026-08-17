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
    c.execute("DELETE FROM goals WHERE user_id = ?", (uid,))
    c.execute("DELETE FROM habits WHERE user_id = ?", (uid,))
    c.execute("DELETE FROM missions WHERE user_id = ?", (uid,))
    c.execute("DELETE FROM app_sessions WHERE user_id = ?", (uid,))
    c.execute("DELETE FROM users WHERE id = ?", (uid,))
    conn.commit()
    conn.close()


def test_search_application_cross_domain_results():
    uid, token = setup_test_user("v2srch_cd")
    try:
        # Create a habit, goal, and mission with keyword 'Alpha'
        client.post("/api/habits", json={"title": "Alpha Habit", "category": "Mindset"}, cookies={"mkc_session": token})
        client.post("/api/goals", json={"title": "Alpha Goal", "category": "Career"}, cookies={"mkc_session": token})
        client.post("/api/missions", json={"title": "Alpha Mission", "category": "Protocol"}, cookies={"mkc_session": token})

        res = client.get("/api/search?q=Alpha", cookies={"mkc_session": token})
        assert res.status_code == 200
        data = res.json()
        assert len(data["habits"]) >= 1
        assert len(data["goals"]) >= 1
        assert len(data["missions"]) >= 1
        assert data["count"] >= 3
    finally:
        cleanup_test_user(uid)


def test_search_application_empty_or_whitespace_query():
    uid, token = setup_test_user("v2srch_emp")
    try:
        res = client.get("/api/search?q=   ", cookies={"mkc_session": token})
        assert res.status_code == 200
        data = res.json()
        assert data["count"] == 0
    finally:
        cleanup_test_user(uid)


def test_update_profile_full_name_and_bio():
    uid, token = setup_test_user("v2prof_upd")
    try:
        res = client.patch(
            "/api/users",
            json={"full_name": "Updated Name", "bio": "Mastery enthusiast"},
            cookies={"mkc_session": token},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["full_name"] == "Updated Name"
        assert data["bio"] == "Mastery enthusiast"

        # Verify via GET /api/users
        res_me = client.get("/api/users", cookies={"mkc_session": token})
        assert res_me.status_code == 200
        assert res_me.json()["full_name"] == "Updated Name"
    finally:
        cleanup_test_user(uid)


def test_update_profile_invalid_email_format_rejected():
    uid, token = setup_test_user("v2prof_invm")
    try:
        res = client.patch(
            "/api/users",
            json={"email": "not-an-email"},
            cookies={"mkc_session": token},
        )
        assert res.status_code == 422
    finally:
        cleanup_test_user(uid)


def test_get_public_profile_nonexistent_user_rejected():
    uid, token = setup_test_user("v2prof_nonex")
    try:
        res = client.get("/api/users/99999999", cookies={"mkc_session": token})
        assert res.status_code == 404
    finally:
        cleanup_test_user(uid)


def test_profile_unauthenticated_guards():
    res_get = client.get("/api/users")
    assert res_get.status_code == 401

    res_patch = client.patch("/api/users", json={"full_name": "Ghost"})
    assert res_patch.status_code == 401

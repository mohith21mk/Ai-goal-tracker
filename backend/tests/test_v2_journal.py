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
    c.execute("DELETE FROM journal_entries WHERE user_id = ?", (uid,))
    c.execute("DELETE FROM app_sessions WHERE user_id = ?", (uid,))
    c.execute("DELETE FROM users WHERE id = ?", (uid,))
    conn.commit()
    conn.close()


def test_save_journal_entry_success():
    uid, token = setup_test_user("v2jrnl_save")
    try:
        res = client.post(
            "/api/journal",
            json={"mood": "energized", "energy_level": 8, "wins_text": "Won today"},
            cookies={"mkc_session": token},
        )
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        data = res.json()
        assert "entry" in data
        assert data["entry"]["mood"] == "energized"
    finally:
        cleanup_test_user(uid)


def test_save_journal_upsert_same_day():
    uid, token = setup_test_user("v2jrnl_upsert")
    try:
        res1 = client.post("/api/journal", json={"mood": "focused", "energy_level": 7}, cookies={"mkc_session": token})
        assert res1.status_code == 200

        res2 = client.post("/api/journal", json={"mood": "energized", "energy_level": 9}, cookies={"mkc_session": token})
        assert res2.status_code == 200

        res3 = client.get("/api/journal/today", cookies={"mkc_session": token})
        assert res3.status_code == 200
        data = res3.json()
        assert data["entry"]["mood"] == "energized"
        assert data["entry"]["energy_level"] == 9
    finally:
        cleanup_test_user(uid)


def test_save_journal_minimal_fields():
    uid, token = setup_test_user("v2jrnl_min")
    try:
        res = client.post("/api/journal", json={"mood": "neutral"}, cookies={"mkc_session": token})
        assert res.status_code == 200
    finally:
        cleanup_test_user(uid)


def test_get_today_entry_exists_and_none():
    uid, token = setup_test_user("v2jrnl_today")
    try:
        # Initially None
        res_none = client.get("/api/journal/today", cookies={"mkc_session": token})
        assert res_none.status_code == 200
        assert res_none.json()["entry"] is None

        # Save and check again
        client.post("/api/journal", json={"mood": "focused", "energy_level": 8}, cookies={"mkc_session": token})
        res_exists = client.get("/api/journal/today", cookies={"mkc_session": token})
        assert res_exists.status_code == 200
        assert res_exists.json()["entry"] is not None
        assert res_exists.json()["entry"]["mood"] == "focused"
    finally:
        cleanup_test_user(uid)


def test_journal_history_and_stats():
    uid, token = setup_test_user("v2jrnl_hstat")
    try:
        client.post("/api/journal", json={"mood": "focused", "energy_level": 8}, cookies={"mkc_session": token})

        res_hist = client.get("/api/journal/history", cookies={"mkc_session": token})
        assert res_hist.status_code == 200
        assert res_hist.json()["count"] >= 1

        res_stats = client.get("/api/journal/stats", cookies={"mkc_session": token})
        assert res_stats.status_code == 200
        assert "total_entries" in res_stats.json()
    finally:
        cleanup_test_user(uid)


def test_analyze_nonexistent_entry():
    uid, token = setup_test_user("v2jrnl_anlz")
    try:
        res = client.post("/api/journal/999999/analyze", cookies={"mkc_session": token})
        assert res.status_code in (404, 500)
    finally:
        cleanup_test_user(uid)


def test_delete_journal_entry_and_isolation():
    uid_a, token_a = setup_test_user("v2jrnl_da")
    uid_b, token_b = setup_test_user("v2jrnl_db")
    try:
        res_create = client.post("/api/journal", json={"mood": "focused"}, cookies={"mkc_session": token_a})
        entry_id = res_create.json()["entry"]["id"]

        # User B cannot delete User A's entry
        res_b_del = client.delete(f"/api/journal/{entry_id}", cookies={"mkc_session": token_b})
        assert res_b_del.status_code == 404

        # User A can delete own entry
        res_a_del = client.delete(f"/api/journal/{entry_id}", cookies={"mkc_session": token_a})
        assert res_a_del.status_code == 200
    finally:
        cleanup_test_user(uid_a)
        cleanup_test_user(uid_b)


def test_journal_unauthenticated_guards():
    res_today = client.get("/api/journal/today")
    assert res_today.status_code == 401

    res_post = client.post("/api/journal", json={"mood": "focused"})
    assert res_post.status_code == 401

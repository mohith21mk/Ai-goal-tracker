import os
import sys
from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from app import create_app
from app.database import get_connection, init_db
from app.services.auth import create_session, hash_password

app = create_app()
client = TestClient(app)


def get_utc_today_str() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


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
    c.execute("DELETE FROM habit_logs WHERE user_id = ?", (uid,))
    c.execute("DELETE FROM habits WHERE user_id = ?", (uid,))
    c.execute("DELETE FROM app_sessions WHERE user_id = ?", (uid,))
    c.execute("DELETE FROM users WHERE id = ?", (uid,))
    conn.commit()
    conn.close()


def test_create_habit_success():
    uid, token = setup_test_user("v2hab_1")
    try:
        res = client.post(
            "/api/habits",
            json={"title": "Drink Water", "category": "Health", "frequency": "daily", "target_days_per_week": 7},
            cookies={"mkc_session": token},
        )
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        data = res.json()
        assert data["title"] == "Drink Water"
        assert data["category"] == "Health"
    finally:
        cleanup_test_user(uid)


def test_create_habit_empty_name():
    uid, token = setup_test_user("v2hab_2")
    try:
        res = client.post(
            "/api/habits",
            json={"title": "", "category": "Health"},
            cookies={"mkc_session": token},
        )
        assert res.status_code in [400, 422], f"Expected validation error, got {res.status_code}"
    finally:
        cleanup_test_user(uid)


def test_list_habits_empty():
    uid, token = setup_test_user("v2hab_3")
    try:
        res = client.get("/api/habits", cookies={"mkc_session": token})
        assert res.status_code == 200
        assert res.json() == []
    finally:
        cleanup_test_user(uid)


def test_list_habits_returns_created():
    uid, token = setup_test_user("v2hab_4")
    try:
        client.post("/api/habits", json={"title": "Test Habit", "category": "Mind"}, cookies={"mkc_session": token})
        res = client.get("/api/habits", cookies={"mkc_session": token})
        assert res.status_code == 200
        data = res.json()
        assert len(data) == 1
        assert data[0]["title"] == "Test Habit"
    finally:
        cleanup_test_user(uid)


def test_get_single_habit():
    uid, token = setup_test_user("v2hab_5")
    try:
        res = client.post("/api/habits", json={"title": "Get Single", "category": "Mind"}, cookies={"mkc_session": token})
        h_id = res.json()["id"]
        res_get = client.get(f"/api/habits/{h_id}", cookies={"mkc_session": token})
        assert res_get.status_code == 200
        assert res_get.json()["title"] == "Get Single"
    finally:
        cleanup_test_user(uid)


def test_get_other_users_habit():
    uid1, token1 = setup_test_user("v2hab_6a")
    uid2, token2 = setup_test_user("v2hab_6b")
    try:
        res = client.post("/api/habits", json={"title": "User 1 Habit", "category": "Mind"}, cookies={"mkc_session": token1})
        h_id = res.json()["id"]
        res_get = client.get(f"/api/habits/{h_id}", cookies={"mkc_session": token2})
        assert res_get.status_code == 404
    finally:
        cleanup_test_user(uid1)
        cleanup_test_user(uid2)


def test_toggle_habit_today():
    uid, token = setup_test_user("v2hab_7")
    try:
        res = client.post("/api/habits", json={"title": "Toggle Today", "category": "Mind"}, cookies={"mkc_session": token})
        h_id = res.json()["id"]
        today = get_utc_today_str()
        res_toggle = client.post(f"/api/habits/{h_id}/toggle", json={"date": today}, cookies={"mkc_session": token})
        assert res_toggle.status_code == 200
        assert res_toggle.json().get("completed") is True
    finally:
        cleanup_test_user(uid)


def test_toggle_habit_twice_untoggle():
    uid, token = setup_test_user("v2hab_8")
    try:
        res = client.post("/api/habits", json={"title": "Toggle Twice", "category": "Mind"}, cookies={"mkc_session": token})
        h_id = res.json()["id"]
        today = get_utc_today_str()
        client.post(f"/api/habits/{h_id}/toggle", json={"date": today}, cookies={"mkc_session": token})
        res_toggle2 = client.post(f"/api/habits/{h_id}/toggle", json={"date": today}, cookies={"mkc_session": token})
        assert res_toggle2.status_code == 200
        assert res_toggle2.json().get("completed") is False
    finally:
        cleanup_test_user(uid)


def test_update_habit_title():
    uid, token = setup_test_user("v2hab_9")
    try:
        res = client.post("/api/habits", json={"title": "Old Title", "category": "Mind"}, cookies={"mkc_session": token})
        h_id = res.json()["id"]
        res_update = client.patch(f"/api/habits/{h_id}", json={"title": "New Title"}, cookies={"mkc_session": token})
        assert res_update.status_code == 200
        assert res_update.json()["title"] == "New Title"
    finally:
        cleanup_test_user(uid)


def test_update_habit_archive():
    uid, token = setup_test_user("v2hab_10")
    try:
        res = client.post("/api/habits", json={"title": "To Archive", "category": "Mind"}, cookies={"mkc_session": token})
        h_id = res.json()["id"]
        res_update = client.patch(f"/api/habits/{h_id}", json={"status": "archived"}, cookies={"mkc_session": token})
        assert res_update.status_code == 200
        assert res_update.json()["status"] == "archived"
    finally:
        cleanup_test_user(uid)


def test_delete_habit_success():
    uid, token = setup_test_user("v2hab_11")
    try:
        res = client.post("/api/habits", json={"title": "To Delete", "category": "Mind"}, cookies={"mkc_session": token})
        h_id = res.json()["id"]
        res_del = client.delete(f"/api/habits/{h_id}", cookies={"mkc_session": token})
        assert res_del.status_code == 200
        res_get = client.get(f"/api/habits/{h_id}", cookies={"mkc_session": token})
        assert res_get.status_code == 404
    finally:
        cleanup_test_user(uid)


def test_delete_habit_cascades_logs():
    uid, token = setup_test_user("v2hab_12")
    try:
        res = client.post("/api/habits", json={"title": "To Delete Casc", "category": "Mind"}, cookies={"mkc_session": token})
        h_id = res.json()["id"]
        today = get_utc_today_str()
        client.post(f"/api/habits/{h_id}/toggle", json={"date": today}, cookies={"mkc_session": token})
        client.delete(f"/api/habits/{h_id}", cookies={"mkc_session": token})
        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM habit_logs WHERE habit_id = ?", (h_id,))
        count = c.fetchone()[0]
        conn.close()
        assert count == 0
    finally:
        cleanup_test_user(uid)


def test_habit_stats_empty():
    uid, token = setup_test_user("v2hab_13")
    try:
        res = client.get("/api/habits/stats", cookies={"mkc_session": token})
        assert res.status_code == 200
    finally:
        cleanup_test_user(uid)


def test_habit_stats_with_data():
    uid, token = setup_test_user("v2hab_14")
    try:
        res = client.post("/api/habits", json={"title": "Stat Habit", "category": "Mind"}, cookies={"mkc_session": token})
        h_id = res.json()["id"]
        today = get_utc_today_str()
        client.post(f"/api/habits/{h_id}/toggle", json={"date": today}, cookies={"mkc_session": token})
        res_stats = client.get("/api/habits/stats", cookies={"mkc_session": token})
        assert res_stats.status_code == 200
        stats = res_stats.json()
        assert stats.get("total_active_habits", 0) >= 1
    finally:
        cleanup_test_user(uid)


def test_habits_unauthenticated():
    uid, _ = setup_test_user("v2hab_15")
    try:
        res = client.get("/api/habits")
        assert res.status_code == 401
    finally:
        cleanup_test_user(uid)


def test_habit_isolation():
    uid1, token1 = setup_test_user("v2hab_16a")
    uid2, token2 = setup_test_user("v2hab_16b")
    try:
        client.post("/api/habits", json={"title": "User 1 Habit", "category": "Mind"}, cookies={"mkc_session": token1})
        res2 = client.get("/api/habits", cookies={"mkc_session": token2})
        assert res2.status_code == 200
        assert len(res2.json()) == 0
    finally:
        cleanup_test_user(uid1)
        cleanup_test_user(uid2)

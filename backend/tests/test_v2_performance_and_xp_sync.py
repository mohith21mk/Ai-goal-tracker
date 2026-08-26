import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_connection
from app.services.progression import get_user_progression, calculate_user_xp
from app.api.progress import compute_telemetry_sync

client = TestClient(app)

TEST_EMAIL = "xp_sync_user@test.com"
TEST_PASS = "SyncPass123!"


@pytest.fixture
def sync_user():
    client.post(
        "/api/auth/register",
        json={
            "full_name": "XP Sync User",
            "username": "xpsync_user",
            "email": TEST_EMAIL,
            "password": TEST_PASS,
            "confirm_password": TEST_PASS,
        },
    )

    login_res = client.post(
        "/api/auth/login",
        json={"identifier": TEST_EMAIL, "password": TEST_PASS},
    )
    user_id = login_res.json()["id"]

    yield {"id": user_id, "cookies": login_res.cookies}

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM habit_logs WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM habits WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM missions WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM app_sessions WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()


def test_mission_and_habit_xp_synchronization(sync_user):
    user_id = sync_user["id"]
    cookies = sync_user["cookies"]

    # 1. Initial progression should be 0 XP, Level 1, Rank INITIATE
    init_prog = client.get("/api/progression", cookies=cookies).json()
    assert init_prog["total_xp"] == 0
    assert init_prog["level"] == 1
    assert init_prog["rank"] == "INITIATE"

    # 2. Create and complete a mission with 50 XP
    m_res = client.post(
        "/api/missions",
        json={"title": "Test Mission 50", "xp_reward": 50, "difficulty": "medium"},
        cookies=cookies,
    )
    assert m_res.status_code == 200
    mission_id = m_res.json()["id"]

    # Toggle mission to completed
    toggle_m = client.patch(f"/api/missions/{mission_id}/toggle", cookies=cookies)
    assert toggle_m.status_code == 200
    assert toggle_m.json()["completed"] is True

    # Check progression: XP should be 50
    prog_after_m = client.get("/api/progression", cookies=cookies).json()
    assert prog_after_m["total_xp"] == 50
    assert prog_after_m["mission_xp"] == 50
    assert prog_after_m["habit_xp"] == 0

    # Check telemetry: xp_earned should match progression total_xp
    telem = client.get("/api/progress/telemetry", cookies=cookies).json()
    assert telem["xp_earned"] == 50
    assert telem["progression"]["total_xp"] == 50

    # 3. Create a habit and toggle completion for today (15 XP)
    h_res = client.post(
        "/api/habits",
        json={"title": "Morning Cold Plunge", "category": "wellness"},
        cookies=cookies,
    )
    assert h_res.status_code == 200
    habit_id = h_res.json()["id"]

    import datetime
    today_str = datetime.date.today().strftime("%Y-%m-%d")

    toggle_h = client.post(
        f"/api/habits/{habit_id}/toggle",
        json={"date": today_str},
        cookies=cookies,
    )
    assert toggle_h.status_code == 200
    assert toggle_h.json()["completed"] is True

    # Check progression: 50 + 15 = 65 XP
    prog_after_h = client.get("/api/progression", cookies=cookies).json()
    assert prog_after_h["total_xp"] == 65
    assert prog_after_h["mission_xp"] == 50
    assert prog_after_h["habit_xp"] == 15

    # Check telemetry sync
    telem_after_h = client.get("/api/progress/telemetry", cookies=cookies).json()
    assert telem_after_h["xp_earned"] == 65
    assert telem_after_h["progression"]["total_xp"] == 65

    # 4. Untoggle habit: XP should decrease back to 50
    untoggle_h = client.post(
        f"/api/habits/{habit_id}/toggle",
        json={"date": today_str},
        cookies=cookies,
    )
    assert untoggle_h.status_code == 200
    assert untoggle_h.json()["completed"] is False

    prog_after_untoggle_h = client.get("/api/progression", cookies=cookies).json()
    assert prog_after_untoggle_h["total_xp"] == 50
    assert prog_after_untoggle_h["habit_xp"] == 0

    # 5. Untoggle mission: XP should return to 0
    untoggle_m = client.patch(f"/api/missions/{mission_id}/toggle", cookies=cookies)
    assert untoggle_m.status_code == 200
    assert untoggle_m.json()["completed"] is False

    prog_zero = client.get("/api/progression", cookies=cookies).json()
    assert prog_zero["total_xp"] == 0
    assert prog_zero["mission_xp"] == 0


def test_completed_3_missions_telemetry_live_update(sync_user):
    cookies = sync_user["cookies"]

    # Create 3 missions (Productivity, Wellness, Learning)
    m1 = client.post(
        "/api/missions",
        json={"title": "morning habit", "category": "productivity", "xp_reward": 50},
        cookies=cookies,
    ).json()["id"]

    m2 = client.post(
        "/api/missions",
        json={"title": "workout", "category": "wellness", "xp_reward": 50},
        cookies=cookies,
    ).json()["id"]

    m3 = client.post(
        "/api/missions",
        json={"title": "learning", "category": "learning", "xp_reward": 50},
        cookies=cookies,
    ).json()["id"]

    # Toggle all 3 missions to completed
    client.patch(f"/api/missions/{m1}/toggle", cookies=cookies)
    client.patch(f"/api/missions/{m2}/toggle", cookies=cookies)
    client.patch(f"/api/missions/{m3}/toggle", cookies=cookies)

    # Fetch live telemetry
    telem = client.get("/api/telemetry", cookies=cookies).json()

    # Verify metrics are not 0
    assert telem["mission_completion"]["completed"] >= 3
    assert telem["mission_completion"]["total"] >= 3
    assert telem["mission_completion"]["percentage"] > 0
    assert telem["xp_earned"] >= 150
    assert telem["discipline_score"] > 0
    assert telem["mindset_strength"] > 0
    assert telem["consistency"] > 0
    assert telem["growth_index"] > 0
    assert telem["streak_days"] >= 1
    assert telem["progression"]["total_xp"] >= 150
    assert telem["progression"]["level"] >= 1


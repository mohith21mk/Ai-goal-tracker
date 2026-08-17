from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient
from app import create_app
from app.database import get_connection
from app.services.auth import hash_password, create_session

app = create_app()
client = TestClient(app)

@pytest.fixture(scope="module")
def setup_multi_users():
    conn = get_connection()
    cursor = conn.cursor()

    # Clean up test users if existing
    cursor.execute("DELETE FROM users WHERE email IN ('sec_user_a@mkc.test', 'sec_user_b@mkc.test', 'sec_empty_user@mkc.test')")
    conn.commit()

    # Create User A
    cursor.execute(
        """
        INSERT INTO users (email, username, password_hash, full_name, mkc_id, email_verified, onboarding_completed)
        VALUES ('sec_user_a@mkc.test', 'sec_user_a', ?, 'User Alpha', 'MKC-SEC-A', 1, 1)
        """,
        (hash_password("Password123!"),)
    )
    user_a_id = cursor.lastrowid

    # Create User B
    cursor.execute(
        """
        INSERT INTO users (email, username, password_hash, full_name, mkc_id, email_verified, onboarding_completed)
        VALUES ('sec_user_b@mkc.test', 'sec_user_b', ?, 'User Beta', 'MKC-SEC-B', 1, 1)
        """,
        (hash_password("Password123!"),)
    )
    user_b_id = cursor.lastrowid

    # Create Empty User
    cursor.execute(
        """
        INSERT INTO users (email, username, password_hash, full_name, mkc_id, email_verified, onboarding_completed)
        VALUES ('sec_empty_user@mkc.test', 'sec_empty_user', ?, 'Empty User', 'MKC-SEC-EMPTY', 1, 1)
        """,
        (hash_password("Password123!"),)
    )
    empty_user_id = cursor.lastrowid

    conn.commit()
    conn.close()

    # Generate active sessions
    session_a = create_session(user_a_id)
    session_b = create_session(user_b_id)
    session_empty = create_session(empty_user_id)

    yield {
        "user_a": {"id": user_a_id, "token": session_a},
        "user_b": {"id": user_b_id, "token": session_b},
        "empty_user": {"id": empty_user_id, "token": session_empty},
    }

    # Teardown
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE id IN (?, ?, ?)", (user_a_id, user_b_id, empty_user_id))
    conn.commit()
    conn.close()


def test_goal_cross_user_isolation(setup_multi_users):
    user_a = setup_multi_users["user_a"]
    user_b = setup_multi_users["user_b"]

    # User B creates a private goal
    res = client.post(
        "/api/goals",
        json={"title": "User B Secret Goal", "category": "career"},
        cookies={"mkc_session": user_b["token"]}
    )
    assert res.status_code == 200
    goal_b_id = res.json()["id"]

    # User A tries to GET User B's goal -> 404 Not Found
    res = client.get(f"/api/goals/{goal_b_id}", cookies={"mkc_session": user_a["token"]})
    assert res.status_code == 404

    # User A tries to PATCH User B's goal -> 404 Not Found
    res = client.patch(f"/api/goals/{goal_b_id}", json={"title": "Hacked Title"}, cookies={"mkc_session": user_a["token"]})
    assert res.status_code == 404

    # User A tries to DELETE User B's goal -> 404 Not Found
    res = client.delete(f"/api/goals/{goal_b_id}", cookies={"mkc_session": user_a["token"]})
    assert res.status_code == 404

    # Verify User B's goal still exists and is untouched
    res = client.get(f"/api/goals/{goal_b_id}", cookies={"mkc_session": user_b["token"]})
    assert res.status_code == 200
    assert res.json()["title"] == "User B Secret Goal"


def test_habit_cross_user_isolation(setup_multi_users):
    user_a = setup_multi_users["user_a"]
    user_b = setup_multi_users["user_b"]

    # User B creates a habit
    res = client.post(
        "/api/habits",
        json={"title": "User B Secret Habit", "frequency": "daily"},
        cookies={"mkc_session": user_b["token"]}
    )
    assert res.status_code == 200
    habit_b_id = res.json()["id"]

    # User A tries to view User B's habit -> 404
    res = client.get(f"/api/habits/{habit_b_id}", cookies={"mkc_session": user_a["token"]})
    assert res.status_code == 404

    # User A tries to toggle User B's habit -> 404
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    res = client.post(
        f"/api/habits/{habit_b_id}/toggle",
        json={"date": today_str},
        cookies={"mkc_session": user_a["token"]}
    )
    assert res.status_code == 404

    # User A tries to delete User B's habit -> 404
    res = client.delete(f"/api/habits/{habit_b_id}", cookies={"mkc_session": user_a["token"]})
    assert res.status_code == 404


def test_mission_cross_user_isolation(setup_multi_users):
    user_a = setup_multi_users["user_a"]
    user_b = setup_multi_users["user_b"]

    # User B creates a mission
    res = client.post(
        "/api/missions",
        json={"title": "User B Mission", "time": "15 min", "difficulty": "easy"},
        cookies={"mkc_session": user_b["token"]}
    )
    assert res.status_code == 200
    mission_b_id = res.json()["id"]

    # User A tries to toggle User B's mission -> 404
    res = client.patch(f"/api/missions/{mission_b_id}/toggle", cookies={"mkc_session": user_a["token"]})
    assert res.status_code == 404


def test_community_ownership_and_credential_spoofing(setup_multi_users):
    user_a = setup_multi_users["user_a"]
    user_b = setup_multi_users["user_b"]

    # User B creates a post
    res = client.post(
        "/api/community/posts",
        json={"content": "Post by User Beta", "category": "general"},
        cookies={"mkc_session": user_b["token"]}
    )
    assert res.status_code == 200
    post_b_id = res.json()["id"]

    # User A tries to edit User B's post -> 403 Forbidden
    res = client.patch(
        f"/api/community/posts/{post_b_id}",
        json={"content": "Hacked content by User A"},
        cookies={"mkc_session": user_a["token"]}
    )
    assert res.status_code == 403

    # User A tries to delete User B's post -> 403 Forbidden
    res = client.delete(f"/api/community/posts/{post_b_id}", cookies={"mkc_session": user_a["token"]})
    assert res.status_code == 403

    # User A tries to forge a non-existent / unauthorized credential ID -> 400 Bad Request
    res = client.post(
        "/api/community/posts",
        json={"content": "Fake verified post", "category": "wins", "credential_id": 999999},
        cookies={"mkc_session": user_a["token"]}
    )
    assert res.status_code == 400


def test_empty_user_state_resilience(setup_multi_users):
    empty_user = setup_multi_users["empty_user"]

    # Telemetry should compute cleanly with 0 missions/habits/goals
    res = client.get("/api/telemetry", cookies={"mkc_session": empty_user["token"]})
    assert res.status_code == 200
    data = res.json()
    assert "discipline_score" in data
    assert "mindset_strength" in data
    assert "consistency" in data
    assert data["streak_days"] == 0

    # Goals, habits, missions list endpoints should return empty arrays without crashing
    res = client.get("/api/goals", cookies={"mkc_session": empty_user["token"]})
    assert res.status_code == 200
    assert res.json() == []

    res = client.get("/api/habits", cookies={"mkc_session": empty_user["token"]})
    assert res.status_code == 200
    assert res.json() == []

    res = client.get("/api/missions", cookies={"mkc_session": empty_user["token"]})
    assert res.status_code == 200
    assert res.json() == []

    # Notifications list and unread count
    res = client.get("/api/notifications", cookies={"mkc_session": empty_user["token"]})
    assert res.status_code == 200
    assert res.json() == []

    res = client.get("/api/notifications/unread-count", cookies={"mkc_session": empty_user["token"]})
    assert res.status_code == 200
    assert res.json()["unread_count"] == 0

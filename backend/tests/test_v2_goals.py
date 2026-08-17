import os, sys
from fastapi.testclient import TestClient
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from app import create_app
from app.database import get_connection, init_db
from app.services.auth import hash_password, create_session

app = create_app()
client = TestClient(app)

def setup_test_user(prefix, role="user"):
    init_db()
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM app_sessions WHERE user_id IN (SELECT id FROM users WHERE email LIKE ?)", (f"{prefix}%",))
    c.execute("DELETE FROM users WHERE email LIKE ?", (f"{prefix}%",))
    conn.commit()
    pwd = hash_password("TestPass123!")
    c.execute(
        "INSERT INTO users (email, username, password_hash, full_name, mkc_id, email_verified, onboarding_completed, avatar_initials) VALUES (?, ?, ?, ?, ?, 1, 1, ?)",
        (f"{prefix}@test.mkc", f"u_{prefix}", pwd, f"Test {prefix}", f"MKC-{prefix.upper()}", "TU")
    )
    uid = c.lastrowid
    conn.commit()
    conn.close()
    token = create_session(uid)
    return uid, token

def cleanup_test_user(uid):
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM goals WHERE user_id = ?", (uid,))
    c.execute("DELETE FROM app_sessions WHERE user_id = ?", (uid,))
    c.execute("DELETE FROM users WHERE id = ?", (uid,))
    conn.commit()
    conn.close()

def test_create_goal_success():
    uid, token = setup_test_user("v2goal_1")
    try:
        data = {
            "title": "Learn FastAPI",
            "description": "Master it",
            "category": "Education",
            "target_date": "2026-12-31"
        }
        res = client.post("/api/goals", json=data, cookies={"mkc_session": token})
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        res_data = res.json()
        assert res_data["title"] == data["title"]
        assert res_data["category"] == data["category"]
    finally:
        cleanup_test_user(uid)

def test_create_goal_missing_title():
    uid, token = setup_test_user("v2goal_2")
    try:
        data = {
            "description": "Master it",
            "category": "Education"
        }
        res = client.post("/api/goals", json=data, cookies={"mkc_session": token})
        assert res.status_code == 422, f"Expected 422, got {res.status_code}: {res.text}"
    finally:
        cleanup_test_user(uid)

def test_create_goal_long_title():
    uid, token = setup_test_user("v2goal_3")
    try:
        data = {
            "title": "A" * 10000,
            "category": "Education"
        }
        res = client.post("/api/goals", json=data, cookies={"mkc_session": token})
        assert res.status_code != 500, f"Expected non-500, got {res.status_code}"
    finally:
        cleanup_test_user(uid)

def test_list_goals_empty():
    uid, token = setup_test_user("v2goal_4")
    try:
        res = client.get("/api/goals", cookies={"mkc_session": token})
        assert res.status_code == 200
        assert len(res.json()) == 0
    finally:
        cleanup_test_user(uid)

def test_list_goals_returns_own():
    uid, token = setup_test_user("v2goal_5")
    try:
        client.post("/api/goals", json={"title": "Goal 1", "category": "Health"}, cookies={"mkc_session": token})
        client.post("/api/goals", json={"title": "Goal 2", "category": "Health"}, cookies={"mkc_session": token})
        
        res = client.get("/api/goals", cookies={"mkc_session": token})
        assert res.status_code == 200
        assert len(res.json()) == 2
    finally:
        cleanup_test_user(uid)

def test_get_goal_by_id():
    uid, token = setup_test_user("v2goal_6")
    try:
        create_res = client.post("/api/goals", json={"title": "Specific", "category": "Health"}, cookies={"mkc_session": token})
        goal_id = create_res.json()["id"]
        
        res = client.get(f"/api/goals/{goal_id}", cookies={"mkc_session": token})
        assert res.status_code == 200
        assert res.json()["title"] == "Specific"
    finally:
        cleanup_test_user(uid)

def test_get_nonexistent_goal():
    uid, token = setup_test_user("v2goal_7")
    try:
        res = client.get("/api/goals/999999", cookies={"mkc_session": token})
        assert res.status_code == 404
    finally:
        cleanup_test_user(uid)

def test_get_other_users_goal():
    uid1, token1 = setup_test_user("v2goal_8a")
    uid2, token2 = setup_test_user("v2goal_8b")
    try:
        create_res = client.post("/api/goals", json={"title": "User 1 Goal", "category": "Health"}, cookies={"mkc_session": token1})
        goal_id = create_res.json()["id"]
        
        res = client.get(f"/api/goals/{goal_id}", cookies={"mkc_session": token2})
        assert res.status_code in [403, 404], f"Expected 403 or 404, got {res.status_code}"
    finally:
        cleanup_test_user(uid1)
        cleanup_test_user(uid2)

def test_update_goal_success():
    uid, token = setup_test_user("v2goal_9")
    try:
        create_res = client.post("/api/goals", json={"title": "Original Title", "category": "Health"}, cookies={"mkc_session": token})
        goal_id = create_res.json()["id"]
        
        res = client.patch(f"/api/goals/{goal_id}", json={"title": "Updated Title"}, cookies={"mkc_session": token})
        assert res.status_code == 200
        assert res.json()["title"] == "Updated Title"
    finally:
        cleanup_test_user(uid)

def test_update_goal_status_completed():
    uid, token = setup_test_user("v2goal_10")
    try:
        create_res = client.post("/api/goals", json={"title": "Goal to complete", "category": "Health"}, cookies={"mkc_session": token})
        goal_id = create_res.json()["id"]
        
        res = client.patch(f"/api/goals/{goal_id}", json={"status": "completed"}, cookies={"mkc_session": token})
        assert res.status_code == 200
        assert res.json()["status"] == "completed"
    finally:
        cleanup_test_user(uid)

def test_update_nonexistent_goal():
    uid, token = setup_test_user("v2goal_11")
    try:
        res = client.patch("/api/goals/999999", json={"title": "Updated Title"}, cookies={"mkc_session": token})
        assert res.status_code == 404
    finally:
        cleanup_test_user(uid)

def test_delete_goal_success():
    uid, token = setup_test_user("v2goal_12")
    try:
        create_res = client.post("/api/goals", json={"title": "Delete Me", "category": "Health"}, cookies={"mkc_session": token})
        goal_id = create_res.json()["id"]
        
        res = client.delete(f"/api/goals/{goal_id}", cookies={"mkc_session": token})
        assert res.status_code == 200
        
        get_res = client.get(f"/api/goals/{goal_id}", cookies={"mkc_session": token})
        assert get_res.status_code == 404
    finally:
        cleanup_test_user(uid)

def test_delete_other_users_goal():
    uid1, token1 = setup_test_user("v2goal_13a")
    uid2, token2 = setup_test_user("v2goal_13b")
    try:
        create_res = client.post("/api/goals", json={"title": "User 1 Goal", "category": "Health"}, cookies={"mkc_session": token1})
        goal_id = create_res.json()["id"]
        
        res = client.delete(f"/api/goals/{goal_id}", cookies={"mkc_session": token2})
        assert res.status_code in [403, 404], f"Expected 403 or 404, got {res.status_code}"
    finally:
        cleanup_test_user(uid1)
        cleanup_test_user(uid2)

def test_delete_nonexistent_goal():
    uid, token = setup_test_user("v2goal_14")
    try:
        res = client.delete("/api/goals/999999", cookies={"mkc_session": token})
        assert res.status_code == 404
    finally:
        cleanup_test_user(uid)

def test_goals_unauthenticated():
    res = client.get("/api/goals")
    assert res.status_code == 401
    
    res2 = client.post("/api/goals", json={"title": "Should Fail", "category": "Health"})
    assert res2.status_code == 401

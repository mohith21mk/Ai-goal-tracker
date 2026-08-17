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
    c.execute("DELETE FROM user_settings WHERE user_id IN (SELECT id FROM users WHERE email LIKE ?)", (f"{prefix}%",))
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
    c.execute("DELETE FROM user_settings WHERE user_id = ?", (uid,))
    c.execute("DELETE FROM app_sessions WHERE user_id = ?", (uid,))
    c.execute("DELETE FROM users WHERE id = ?", (uid,))
    conn.commit()
    conn.close()

def test_get_default_settings():
    uid, token = setup_test_user("v2set_dflt")
    try:
        res = client.get("/api/settings", cookies={"mkc_session": token})
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        data = res.json()
        assert "theme" in data
        assert "notifications_enabled" in data
        assert "coach_style" in data
    finally:
        cleanup_test_user(uid)

def test_update_theme_dark():
    uid, token = setup_test_user("v2set_dark")
    try:
        res = client.patch("/api/settings", json={"theme": "dark"}, cookies={"mkc_session": token})
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        
        res2 = client.get("/api/settings", cookies={"mkc_session": token})
        assert res2.json()["theme"] == "dark"
    finally:
        cleanup_test_user(uid)

def test_update_theme_light():
    uid, token = setup_test_user("v2set_light")
    try:
        res = client.patch("/api/settings", json={"theme": "light"}, cookies={"mkc_session": token})
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        
        res2 = client.get("/api/settings", cookies={"mkc_session": token})
        assert res2.json()["theme"] == "light"
    finally:
        cleanup_test_user(uid)

def test_update_notifications_enabled():
    uid, token = setup_test_user("v2set_noti")
    try:
        res = client.patch("/api/settings", json={"notifications_enabled": False}, cookies={"mkc_session": token})
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        
        res2 = client.get("/api/settings", cookies={"mkc_session": token})
        assert res2.json()["notifications_enabled"] is False
    finally:
        cleanup_test_user(uid)

def test_update_coach_style():
    uid, token = setup_test_user("v2set_coach")
    try:
        res = client.patch("/api/settings", json={"coach_style": "strategic"}, cookies={"mkc_session": token})
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        
        res2 = client.get("/api/settings", cookies={"mkc_session": token})
        assert res2.json()["coach_style"] == "strategic"
    finally:
        cleanup_test_user(uid)

def test_update_multiple_settings():
    uid, token = setup_test_user("v2set_mult")
    try:
        payload = {
            "theme": "dark",
            "notifications_enabled": True,
            "coach_style": "empathetic",
            "reminder_time": "08:00",
            "profile_visibility": "public"
        }
        res = client.patch("/api/settings", json=payload, cookies={"mkc_session": token})
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        
        res2 = client.get("/api/settings", cookies={"mkc_session": token})
        data = res2.json()
        assert data["theme"] == "dark"
        assert data["notifications_enabled"] is True
        assert data["coach_style"] == "empathetic"
        if "reminder_time" in data:
            assert data["reminder_time"] == "08:00"
        if "profile_visibility" in data:
            assert data["profile_visibility"] == "public"
    finally:
        cleanup_test_user(uid)

def test_settings_unauthenticated():
    res = client.get("/api/settings")
    assert res.status_code == 401
    
    res = client.patch("/api/settings", json={"theme": "dark"})
    assert res.status_code == 401

def test_settings_isolation():
    uid1, token1 = setup_test_user("v2set_iso1")
    uid2, token2 = setup_test_user("v2set_iso2")
    try:
        client.patch("/api/settings", json={"theme": "dark"}, cookies={"mkc_session": token1})
        client.patch("/api/settings", json={"theme": "light"}, cookies={"mkc_session": token2})
        
        res1 = client.get("/api/settings", cookies={"mkc_session": token1})
        assert res1.json()["theme"] == "dark"
        
        res2 = client.get("/api/settings", cookies={"mkc_session": token2})
        assert res2.json()["theme"] == "light"
    finally:
        cleanup_test_user(uid1)
        cleanup_test_user(uid2)

def test_complete_onboarding_success():
    uid, token = setup_test_user("v2set_onbd")
    try:
        # User needs onboarding_completed=0, setup_test_user sets it to 1, we update it to 0
        conn = get_connection()
        c = conn.cursor()
        c.execute("UPDATE users SET onboarding_completed = 0 WHERE id = ?", (uid,))
        conn.commit()
        conn.close()

        payload = {
            "goals": ["fitness", "learning"],
            "commitment_level": "high",
            "experience_level": "intermediate"
        }
        res = client.post("/api/users/onboarding", json=payload, cookies={"mkc_session": token})
        assert res.status_code in [200, 201], f"Expected 200 or 201, got {res.status_code}: {res.text}"
        
        # Verify onboarding_completed flag
        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT onboarding_completed FROM users WHERE id = ?", (uid,))
        row = c.fetchone()
        conn.close()
        assert row[0] == 1, "Onboarding completed flag not set"
    finally:
        cleanup_test_user(uid)

def test_onboarding_unauthenticated():
    res = client.post("/api/users/onboarding", json={"goals": []})
    assert res.status_code == 401

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
    c.execute("DELETE FROM app_sessions WHERE user_id = ?", (uid,))
    c.execute("DELETE FROM users WHERE id = ?", (uid,))
    conn.commit()
    conn.close()


def cleanup_by_email(email: str):
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM app_sessions WHERE user_id IN (SELECT id FROM users WHERE email = ?)", (email,))
    c.execute("DELETE FROM users WHERE email = ?", (email,))
    conn.commit()
    conn.close()


def test_login_wrong_password():
    uid, _ = setup_test_user("v2auth_lwp")
    try:
        res = client.post("/api/auth/login", json={"identifier": "v2auth_lwp@test.mkc", "password": "WrongPassword!"})
        assert res.status_code == 401, f"Expected 401, got {res.status_code}: {res.text}"
    finally:
        cleanup_test_user(uid)


def test_login_nonexistent_user():
    res = client.post("/api/auth/login", json={"identifier": "nonexistent_user_9999@test.mkc", "password": "TestPass123!"})
    assert res.status_code == 401, f"Expected 401, got {res.status_code}: {res.text}"


def test_login_empty_credentials():
    res = client.post("/api/auth/login", json={"identifier": "", "password": ""})
    assert res.status_code in [400, 401, 422]


def test_register_duplicate_email():
    uid, _ = setup_test_user("v2auth_dup_em")
    try:
        res = client.post("/api/auth/register", json={
            "full_name": "Duplicate Email User",
            "email": "v2auth_dup_em@test.mkc",
            "password": "NewPassword123!",
            "username": "v2auth_dup_em_new"
        })
        assert res.status_code in [400, 409], f"Expected 400 or 409, got {res.status_code}"
    finally:
        cleanup_test_user(uid)


def test_register_duplicate_username():
    uid, _ = setup_test_user("v2auth_dup_un")
    try:
        res = client.post("/api/auth/register", json={
            "full_name": "Duplicate Username User",
            "email": "v2auth_dup_un_new@test.mkc",
            "password": "NewPassword123!",
            "username": "u_v2auth_dup_un"
        })
        assert res.status_code in [400, 409], f"Expected 400 or 409, got {res.status_code}"
    finally:
        cleanup_test_user(uid)


def test_register_invalid_email():
    res = client.post("/api/auth/register", json={
        "full_name": "Invalid Email User",
        "email": "notanemail",
        "password": "NewPassword123!",
        "username": "v2auth_invalid_em"
    })
    assert res.status_code in [400, 422]
    cleanup_by_email("notanemail")


def test_me_without_auth():
    res = client.get("/api/auth/me")
    assert res.status_code == 401


def test_me_with_invalid_session():
    res = client.get("/api/auth/me", cookies={"mkc_session": "garbage_token"})
    assert res.status_code == 401


def test_change_password_success():
    uid, token = setup_test_user("v2auth_cpw")
    try:
        res = client.post("/api/auth/change-password", json={
            "current_password": "TestPass123!",
            "new_password": "NewPassword456!"
        }, cookies={"mkc_session": token})
        assert res.status_code == 200
    finally:
        cleanup_test_user(uid)


def test_change_password_wrong_current():
    uid, token = setup_test_user("v2auth_cpw_wrong")
    try:
        res = client.post("/api/auth/change-password", json={
            "current_password": "WrongPassword123!",
            "new_password": "NewPassword456!"
        }, cookies={"mkc_session": token})
        assert res.status_code in [400, 401, 403]
    finally:
        cleanup_test_user(uid)


def test_forgot_password_nonexistent():
    res = client.post("/api/auth/forgot-password", json={"identifier": "v2auth_nobody@test.mkc"})
    assert res.status_code == 200


def test_reset_password_invalid_token():
    res = client.post("/api/auth/reset-password", json={
        "token": "garbage_token",
        "new_password": "NewPassword123!"
    })
    assert res.status_code in [400, 404]


def test_verify_email_invalid_token():
    res = client.post("/api/auth/verify-email", json={"token": "garbage_token"})
    assert res.status_code in [400, 404]


def test_logout_clears_session():
    uid, token = setup_test_user("v2auth_logout")
    try:
        res = client.post("/api/auth/logout", cookies={"mkc_session": token})
        assert res.status_code == 200
        me_res = client.get("/api/auth/me", cookies={"mkc_session": token})
        assert me_res.status_code == 401
    finally:
        cleanup_test_user(uid)


def test_session_list():
    uid, token = setup_test_user("v2auth_sessions")
    try:
        res = client.get("/api/auth/sessions", cookies={"mkc_session": token})
        assert res.status_code == 200
        assert "sessions" in res.json()
        assert isinstance(res.json()["sessions"], list)
        assert len(res.json()["sessions"]) >= 1
    finally:
        cleanup_test_user(uid)


def test_revoke_other_sessions():
    uid, token1 = setup_test_user("v2auth_revoke")
    token2 = create_session(uid)
    try:
        res = client.post("/api/auth/sessions/revoke-others", cookies={"mkc_session": token1})
        if res.status_code != 404:
            assert res.status_code == 200
            me_res1 = client.get("/api/auth/me", cookies={"mkc_session": token1})
            assert me_res1.status_code == 200
            me_res2 = client.get("/api/auth/me", cookies={"mkc_session": token2})
            assert me_res2.status_code == 401
    finally:
        cleanup_test_user(uid)


def test_deactivate_account():
    uid, token = setup_test_user("v2auth_deact")
    try:
        res = client.post("/api/auth/deactivate", cookies={"mkc_session": token})
        if res.status_code != 404:
            assert res.status_code == 200
            me_res = client.get("/api/auth/me", cookies={"mkc_session": token})
            assert me_res.status_code == 401
    finally:
        cleanup_test_user(uid)

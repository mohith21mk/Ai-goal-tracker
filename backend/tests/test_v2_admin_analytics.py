import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_connection

client = TestClient(app)

ADMIN_EMAIL = "admin_test_owner@mkc.com"
USER_EMAIL = "regular_test_user@mkc.com"
TEST_PASS = "AdminSecurePass123!"


@pytest.fixture
def admin_and_user():
    # 1. Register regular user
    client.post(
        "/api/auth/register",
        json={
            "full_name": "Regular User",
            "username": "reg_user",
            "email": USER_EMAIL,
            "password": TEST_PASS,
            "confirm_password": TEST_PASS,
        },
    )

    # 2. Register admin user
    client.post(
        "/api/auth/register",
        json={
            "full_name": "Admin Owner",
            "username": "admin_owner",
            "email": ADMIN_EMAIL,
            "password": TEST_PASS,
            "confirm_password": TEST_PASS,
        },
    )

    # Promote admin user in DB
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET role = 'admin' WHERE email = ?", (ADMIN_EMAIL,))
    conn.commit()
    conn.close()

    # Login regular user
    reg_login = client.post(
        "/api/auth/login",
        json={"identifier": USER_EMAIL, "password": TEST_PASS},
    )
    reg_cookies = reg_login.cookies
    reg_id = reg_login.json()["id"]

    # Login admin user
    adm_login = client.post(
        "/api/auth/login",
        json={"identifier": ADMIN_EMAIL, "password": TEST_PASS},
    )
    adm_cookies = adm_login.cookies
    adm_id = adm_login.json()["id"]

    yield {
        "reg_id": reg_id,
        "reg_cookies": reg_cookies,
        "adm_id": adm_id,
        "adm_cookies": adm_cookies,
    }

    # Cleanup
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM feedback WHERE user_id IN (?, ?)", (reg_id, adm_id))
    cursor.execute("DELETE FROM habit_logs WHERE user_id IN (?, ?)", (reg_id, adm_id))
    cursor.execute("DELETE FROM habits WHERE user_id IN (?, ?)", (reg_id, adm_id))
    cursor.execute("DELETE FROM missions WHERE user_id IN (?, ?)", (reg_id, adm_id))
    cursor.execute("DELETE FROM app_sessions WHERE user_id IN (?, ?)", (reg_id, adm_id))
    cursor.execute("DELETE FROM users WHERE id IN (?, ?)", (reg_id, adm_id))
    conn.commit()
    conn.close()


def test_admin_access_control(admin_and_user):
    reg_cookies = admin_and_user["reg_cookies"]
    adm_cookies = admin_and_user["adm_cookies"]

    # Regular user is forbidden (403)
    res_reg = client.get("/api/admin/overview", cookies=reg_cookies)
    assert res_reg.status_code == 403

    res_reg_users = client.get("/api/admin/users", cookies=reg_cookies)
    assert res_reg_users.status_code == 403

    # Admin user is granted access (200)
    res_adm = client.get("/api/admin/overview", cookies=adm_cookies)
    assert res_adm.status_code == 200
    overview = res_adm.json()
    assert "total_users" in overview
    assert "active_users_7d" in overview
    assert "user_growth_timeline" in overview
    assert "engagement" in overview
    assert "feedback" in overview


def test_admin_users_directory_and_actions(admin_and_user):
    adm_cookies = admin_and_user["adm_cookies"]
    reg_id = admin_and_user["reg_id"]

    # List users
    users_res = client.get("/api/admin/users?limit=10", cookies=adm_cookies)
    assert users_res.status_code == 200
    data = users_res.json()
    assert "items" in data
    assert "total" in data
    assert len(data["items"]) >= 2

    # Search user
    search_res = client.get("/api/admin/users?q=reg_user", cookies=adm_cookies)
    assert search_res.status_code == 200
    found = search_res.json()["items"]
    assert len(found) == 1
    assert found[0]["email"] == USER_EMAIL
    assert "total_xp" in found[0]
    assert "level" in found[0]
    assert "rank" in found[0]

    # Promote regular user to admin
    role_res = client.patch(
        f"/api/admin/users/{reg_id}/role",
        json={"role": "admin"},
        cookies=adm_cookies,
    )
    assert role_res.status_code == 200
    assert role_res.json()["role"] == "admin"

    # Demote back to user
    role_demote = client.patch(
        f"/api/admin/users/{reg_id}/role",
        json={"role": "user"},
        cookies=adm_cookies,
    )
    assert role_demote.status_code == 200
    assert role_demote.json()["role"] == "user"


def test_admin_feedback_moderation_flow(admin_and_user):
    reg_cookies = admin_and_user["reg_cookies"]
    adm_cookies = admin_and_user["adm_cookies"]

    # User submits feedback
    sub_res = client.post(
        "/api/feedback",
        json={
            "category": "Feature Request",
            "message": "Please add weekly email summary reports.",
            "severity": "Normal",
            "page_url": "/dashboard",
        },
        cookies=reg_cookies,
    )
    assert sub_res.status_code == 201
    feedback_id = sub_res.json()["id"]

    # Admin lists feedback
    fb_list = client.get("/api/admin/feedback", cookies=adm_cookies)
    assert fb_list.status_code == 200
    items = fb_list.json()["items"]
    matching = [item for item in items if item["id"] == feedback_id]
    assert len(matching) == 1
    assert matching[0]["status"] == "new"

    # Admin updates status to 'reviewed'
    patch_res = client.patch(
        f"/api/admin/feedback/{feedback_id}",
        json={"status": "reviewing", "admin_notes": "Queued for Q3 roadmap"},
        cookies=adm_cookies,
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["status"] == "reviewing"

    # Admin updates status to 'resolved'
    resolve_res = client.patch(
        f"/api/admin/feedback/{feedback_id}",
        json={"status": "resolved"},
        cookies=adm_cookies,
    )
    assert resolve_res.status_code == 200
    assert resolve_res.json()["status"] == "resolved"

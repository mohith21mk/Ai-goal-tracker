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
    c.execute("DELETE FROM blueprint_milestones WHERE phase_id IN (SELECT id FROM blueprint_phases WHERE blueprint_id IN (SELECT id FROM life_blueprints WHERE user_id IN (SELECT id FROM users WHERE email LIKE ?)))", (f"{prefix}%",))
    c.execute("DELETE FROM blueprint_phases WHERE blueprint_id IN (SELECT id FROM life_blueprints WHERE user_id IN (SELECT id FROM users WHERE email LIKE ?))", (f"{prefix}%",))
    c.execute("DELETE FROM blueprint_areas WHERE blueprint_id IN (SELECT id FROM life_blueprints WHERE user_id IN (SELECT id FROM users WHERE email LIKE ?))", (f"{prefix}%",))
    c.execute("DELETE FROM life_blueprints WHERE user_id IN (SELECT id FROM users WHERE email LIKE ?)", (f"{prefix}%",))
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
    c.execute("DELETE FROM blueprint_milestones WHERE phase_id IN (SELECT id FROM blueprint_phases WHERE blueprint_id IN (SELECT id FROM life_blueprints WHERE user_id = ?))", (uid,))
    c.execute("DELETE FROM blueprint_phases WHERE blueprint_id IN (SELECT id FROM life_blueprints WHERE user_id = ?)", (uid,))
    c.execute("DELETE FROM blueprint_areas WHERE blueprint_id IN (SELECT id FROM life_blueprints WHERE user_id = ?)", (uid,))
    c.execute("DELETE FROM life_blueprints WHERE user_id = ?", (uid,))
    c.execute("DELETE FROM app_sessions WHERE user_id = ?", (uid,))
    c.execute("DELETE FROM users WHERE id = ?", (uid,))
    conn.commit()
    conn.close()


def test_create_blueprint_success():
    uid, token = setup_test_user("v2bp_cbs")
    try:
        res = client.post(
            "/api/blueprints",
            json={"title": "Mastery Blueprint", "description": "Desc", "vision": "Vision", "target_date": "2028-12-31"},
            cookies={"mkc_session": token},
        )
        assert res.status_code == 201, f"Expected 201, got {res.status_code}: {res.text}"
        data = res.json()
        assert "blueprint" in data
        assert data["blueprint"]["title"] == "Mastery Blueprint"
    finally:
        cleanup_test_user(uid)


def test_list_blueprints_empty_and_after_create():
    uid, token = setup_test_user("v2bp_list")
    try:
        # Empty state
        res_empty = client.get("/api/blueprints", cookies={"mkc_session": token})
        assert res_empty.status_code == 200
        assert res_empty.json()["count"] == 0

        # Create
        client.post("/api/blueprints", json={"title": "BP Alpha"}, cookies={"mkc_session": token})

        # List after create
        res_list = client.get("/api/blueprints", cookies={"mkc_session": token})
        assert res_list.status_code == 200
        assert res_list.json()["count"] == 1
        assert res_list.json()["blueprints"][0]["title"] == "BP Alpha"
    finally:
        cleanup_test_user(uid)


def test_get_blueprint_by_id_and_active():
    uid, token = setup_test_user("v2bp_get")
    try:
        res_create = client.post("/api/blueprints", json={"title": "Active BP"}, cookies={"mkc_session": token})
        bp_id = res_create.json()["blueprint"]["id"]

        # Get by ID
        res_get = client.get(f"/api/blueprints/{bp_id}", cookies={"mkc_session": token})
        assert res_get.status_code == 200
        assert res_get.json()["blueprint"]["id"] == bp_id

        # Get active
        res_act = client.get("/api/blueprints/active", cookies={"mkc_session": token})
        assert res_act.status_code == 200
        assert res_act.json()["blueprint"]["id"] == bp_id
    finally:
        cleanup_test_user(uid)


def test_update_and_delete_blueprint():
    uid, token = setup_test_user("v2bp_updel")
    try:
        res_create = client.post("/api/blueprints", json={"title": "Original BP"}, cookies={"mkc_session": token})
        bp_id = res_create.json()["blueprint"]["id"]

        # Update
        res_upd = client.patch(f"/api/blueprints/{bp_id}", json={"title": "Updated Title"}, cookies={"mkc_session": token})
        assert res_upd.status_code == 200
        assert res_upd.json()["blueprint"]["title"] == "Updated Title"

        # Delete
        res_del = client.delete(f"/api/blueprints/{bp_id}", cookies={"mkc_session": token})
        assert res_del.status_code == 200

        # Get 404 after delete
        res_get = client.get(f"/api/blueprints/{bp_id}", cookies={"mkc_session": token})
        assert res_get.status_code == 404
    finally:
        cleanup_test_user(uid)


def test_phases_and_milestones_full_lifecycle():
    uid, token = setup_test_user("v2bp_phms")
    try:
        res_bp = client.post("/api/blueprints", json={"title": "Phase Testing BP"}, cookies={"mkc_session": token})
        bp_id = res_bp.json()["blueprint"]["id"]

        # Add Phase
        res_phase = client.post(
            f"/api/blueprints/{bp_id}/phases",
            json={"title": "Phase 1: Foundation", "description": "First steps"},
            cookies={"mkc_session": token},
        )
        assert res_phase.status_code == 201
        phases = res_phase.json()["blueprint"]["phases"]
        phase_id = phases[0]["id"]

        # Update Phase
        res_phase_upd = client.patch(
            f"/api/blueprints/phases/{phase_id}",
            json={"title": "Phase 1: Deep Foundation"},
            cookies={"mkc_session": token},
        )
        assert res_phase_upd.status_code == 200

        # Add Milestone
        res_ms = client.post(
            f"/api/blueprints/phases/{phase_id}/milestones",
            json={"title": "Read 5 Books", "target_date": "2026-06-30"},
            cookies={"mkc_session": token},
        )
        assert res_ms.status_code == 201
        milestones = res_ms.json()["blueprint"]["phases"][0]["milestones"]
        ms_id = milestones[0]["id"]

        # Toggle Milestone
        res_tg = client.post(f"/api/blueprints/milestones/{ms_id}/toggle", cookies={"mkc_session": token})
        assert res_tg.status_code == 200

        # Delete Milestone
        res_del_ms = client.delete(f"/api/blueprints/milestones/{ms_id}", cookies={"mkc_session": token})
        assert res_del_ms.status_code == 200

        # Delete Phase
        res_del_ph = client.delete(f"/api/blueprints/phases/{phase_id}", cookies={"mkc_session": token})
        assert res_del_ph.status_code == 200
    finally:
        cleanup_test_user(uid)


def test_blueprint_isolation_between_users():
    uid_a, token_a = setup_test_user("v2bp_ua")
    uid_b, token_b = setup_test_user("v2bp_ub")
    try:
        res_a = client.post("/api/blueprints", json={"title": "User A Private BP"}, cookies={"mkc_session": token_a})
        bp_a_id = res_a.json()["blueprint"]["id"]

        # User B cannot get User A's blueprint
        res_b_get = client.get(f"/api/blueprints/{bp_a_id}", cookies={"mkc_session": token_b})
        assert res_b_get.status_code == 404

        # User B cannot delete User A's blueprint
        res_b_del = client.delete(f"/api/blueprints/{bp_a_id}", cookies={"mkc_session": token_b})
        assert res_b_del.status_code == 404
    finally:
        cleanup_test_user(uid_a)
        cleanup_test_user(uid_b)


def test_blueprint_unauthenticated_guards():
    res_list = client.get("/api/blueprints")
    assert res_list.status_code == 401

    res_post = client.post("/api/blueprints", json={"title": "No Auth"})
    assert res_post.status_code == 401

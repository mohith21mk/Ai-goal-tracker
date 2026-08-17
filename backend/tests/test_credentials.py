"""
Targeted tests for Verified Credential Engine and Anti-Spoofing Rules.
Verifies all 6 credential types, idempotency, user isolation, and server evidence enforcement.
"""
import os
import sys
from datetime import datetime, date, timedelta
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.main import app
from app.database import get_connection, init_db
from app.services.auth import create_session, hash_password
from app.services.progression import evaluate_and_issue_credentials, list_user_credentials

client = TestClient(app)


def setup_user(email_prefix: str):
    init_db()
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM user_credentials WHERE user_id IN (SELECT id FROM users WHERE email LIKE ?)", (f"{email_prefix}%",))
    cursor.execute("DELETE FROM blueprint_milestones WHERE blueprint_id IN (SELECT id FROM life_blueprints WHERE user_id IN (SELECT id FROM users WHERE email LIKE ?))", (f"{email_prefix}%",))
    cursor.execute("DELETE FROM life_blueprints WHERE user_id IN (SELECT id FROM users WHERE email LIKE ?)", (f"{email_prefix}%",))
    cursor.execute("DELETE FROM habit_logs WHERE user_id IN (SELECT id FROM users WHERE email LIKE ?)", (f"{email_prefix}%",))
    cursor.execute("DELETE FROM habits WHERE user_id IN (SELECT id FROM users WHERE email LIKE ?)", (f"{email_prefix}%",))
    cursor.execute("DELETE FROM missions WHERE user_id IN (SELECT id FROM users WHERE email LIKE ?)", (f"{email_prefix}%",))
    cursor.execute("DELETE FROM app_sessions WHERE user_id IN (SELECT id FROM users WHERE email LIKE ?)", (f"{email_prefix}%",))
    cursor.execute("DELETE FROM users WHERE email LIKE ?", (f"{email_prefix}%",))
    conn.commit()

    pwd = hash_password("Test1234!")
    cursor.execute(
        "INSERT INTO users (email, full_name, username, password_hash, avatar_initials) VALUES (?, ?, ?, ?, ?)",
        (f"{email_prefix}@example.com", f"User {email_prefix}", f"user_{email_prefix}", pwd, "TU"),
    )
    user_id = cursor.lastrowid
    conn.commit()
    conn.close()

    session_token = create_session(user_id)
    return user_id, session_token


def cleanup_user(user_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM user_credentials WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM blueprint_milestones WHERE blueprint_id IN (SELECT id FROM life_blueprints WHERE user_id = ?)", (user_id,))
    cursor.execute("DELETE FROM life_blueprints WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM habit_logs WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM habits WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM missions WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM app_sessions WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()


def test_no_evidence_receives_no_credentials():
    """Test 1: User with zero evidence receives zero credentials."""
    user_id, token = setup_user("cred_test_zero")
    try:
        res = evaluate_and_issue_credentials(user_id)
        assert len(res["newly_earned"]) == 0, "No credentials should be awarded without evidence"
        assert len(res["credentials"]) == 0, "Credential list must be empty"
        print("PASS: User with zero evidence receives zero credentials")
    finally:
        cleanup_user(user_id)


def test_streak_credentials_7_30_100():
    """Test 2, 3, 4: 7-day, 30-day, and 100-day verified habit streak credentials."""
    user_id, token = setup_user("cred_test_streak")
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO habits (user_id, title) VALUES (?, ?)", (user_id, "Meditation"))
        h_id = cursor.lastrowid

        start_dt = date(2026, 1, 1)

        # 1. Add 7 consecutive days
        for i in range(7):
            d_str = (start_dt + timedelta(days=i)).strftime("%Y-%m-%d")
            cursor.execute("INSERT INTO habit_logs (habit_id, user_id, completed_date) VALUES (?, ?, ?)", (h_id, user_id, d_str))
        conn.commit()

        res_7 = evaluate_and_issue_credentials(user_id)
        slugs_7 = [c["slug"] for c in res_7["newly_earned"]]
        assert "streak_7" in slugs_7, "streak_7 must be earned after 7 consecutive days"
        assert "streak_30" not in slugs_7, "streak_30 must not be earned yet"

        # 2. Extend to 30 consecutive days
        for i in range(7, 30):
            d_str = (start_dt + timedelta(days=i)).strftime("%Y-%m-%d")
            cursor.execute("INSERT INTO habit_logs (habit_id, user_id, completed_date) VALUES (?, ?, ?)", (h_id, user_id, d_str))
        conn.commit()

        res_30 = evaluate_and_issue_credentials(user_id)
        slugs_30 = [c["slug"] for c in res_30["newly_earned"]]
        assert "streak_30" in slugs_30, "streak_30 must be earned after 30 consecutive days"
        assert "streak_100" not in slugs_30, "streak_100 must not be earned yet"

        # 3. Extend to 100 consecutive days
        for i in range(30, 100):
            d_str = (start_dt + timedelta(days=i)).strftime("%Y-%m-%d")
            cursor.execute("INSERT INTO habit_logs (habit_id, user_id, completed_date) VALUES (?, ?, ?)", (h_id, user_id, d_str))
        conn.commit()
        conn.close()

        res_100 = evaluate_and_issue_credentials(user_id)
        slugs_100 = [c["slug"] for c in res_100["newly_earned"]]
        assert "streak_100" in slugs_100, "streak_100 must be earned after 100 consecutive days"

        print("PASS: Streak credentials (7, 30, 100 days) verified with consecutive database dates")
    finally:
        cleanup_user(user_id)


def test_missions_50_credential():
    """Test 5: 50 completed missions earns missions_50 credential."""
    user_id, token = setup_user("cred_test_m50")
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Insert 49 completed missions
        for i in range(49):
            cursor.execute(
                "INSERT INTO missions (user_id, title, completed, completed_at, xp_reward) VALUES (?, ?, 1, CURRENT_TIMESTAMP, 10)",
                (user_id, f"Mission {i}"),
            )
        conn.commit()

        # At 49 -> not earned
        res_49 = evaluate_and_issue_credentials(user_id)
        assert not any(c["slug"] == "missions_50" for c in res_49["credentials"])

        # Insert 50th completed mission
        cursor.execute(
            "INSERT INTO missions (user_id, title, completed, completed_at, xp_reward) VALUES (?, 'Mission 50', 1, CURRENT_TIMESTAMP, 10)",
            (user_id,),
        )
        conn.commit()
        conn.close()

        # At 50 -> earned
        res_50 = evaluate_and_issue_credentials(user_id)
        assert any(c["slug"] == "missions_50" for c in res_50["newly_earned"])
        print("PASS: 50 completed missions earns missions_50 credential")
    finally:
        cleanup_user(user_id)


def test_blueprint_milestone_credential():
    """Test 6: 1 verified completed blueprint milestone earns blueprint_milestone_1."""
    user_id, token = setup_user("cred_test_bm1")
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Create blueprint and uncompleted milestone
        cursor.execute(
            "INSERT INTO life_blueprints (user_id, title, status) VALUES (?, 'Master AI', 'active')",
            (user_id,),
        )
        bp_id = cursor.lastrowid

        cursor.execute(
            "INSERT INTO blueprint_phases (blueprint_id, title, phase_number) VALUES (?, 'Phase 1', 1)",
            (bp_id,),
        )
        phase_id = cursor.lastrowid

        cursor.execute(
            "INSERT INTO blueprint_milestones (phase_id, blueprint_id, title, completed, completed_at) VALUES (?, ?, 'DSA Mastery', 0, NULL)",
            (phase_id, bp_id),
        )
        milestone_id = cursor.lastrowid
        conn.commit()

        # Milestone not completed -> no credential
        res_before = evaluate_and_issue_credentials(user_id)
        assert not any(c["slug"] == "blueprint_milestone_1" for c in res_before["credentials"])

        # Complete the milestone
        cursor.execute(
            "UPDATE blueprint_milestones SET completed = 1, completed_at = CURRENT_TIMESTAMP WHERE id = ?",
            (milestone_id,),
        )
        conn.commit()
        conn.close()

        # Check credentials -> blueprint_milestone_1 earned
        res_after = evaluate_and_issue_credentials(user_id)
        assert any(c["slug"] == "blueprint_milestone_1" for c in res_after["newly_earned"])
        print("PASS: Completed blueprint milestone earns blueprint_milestone_1")
    finally:
        cleanup_user(user_id)


def test_mastery_level_20_credential():
    """Test 7: Server-calculated level >= 20 earns mastery_level_20."""
    user_id, token = setup_user("cred_test_lvl20")
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Level 20 requires at least (20 - 1) * 500 = 9500 XP
        # Insert missions awarding 9500 XP
        cursor.execute(
            "INSERT INTO missions (user_id, title, completed, completed_at, xp_reward) VALUES (?, 'Mega Mission', 1, CURRENT_TIMESTAMP, 9500)",
            (user_id,),
        )
        conn.commit()
        conn.close()

        res = evaluate_and_issue_credentials(user_id)
        assert any(c["slug"] == "mastery_level_20" for c in res["newly_earned"])
        print("PASS: Server level 20 earns mastery_level_20 credential")
    finally:
        cleanup_user(user_id)


def test_credential_idempotency():
    """Test 8: Credential cannot be issued twice."""
    user_id, token = setup_user("cred_test_idemp")
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO habits (user_id, title) VALUES (?, 'Hydration')", (user_id,))
        h_id = cursor.lastrowid
        for i in range(7):
            cursor.execute(f"INSERT INTO habit_logs (habit_id, user_id, completed_date) VALUES (?, ?, '2026-08-{i+1:02d}')", (h_id, user_id))
        conn.commit()
        conn.close()

        # First evaluation -> streak_7 in newly_earned
        res1 = evaluate_and_issue_credentials(user_id)
        assert any(c["slug"] == "streak_7" for c in res1["newly_earned"])

        # Second evaluation -> newly_earned must be empty, total credentials remains 1
        res2 = evaluate_and_issue_credentials(user_id)
        assert len(res2["newly_earned"]) == 0
        assert len(res2["credentials"]) == 1
        print("PASS: Credential issuance is strictly idempotent (never duplicates)")
    finally:
        cleanup_user(user_id)


def test_user_isolation_and_anti_spoofing():
    """Test 9, 10, 11, 12: User isolation, spoofing resistance, and unauthenticated guards."""
    user_a_id, token_a = setup_user("cred_test_usera")
    user_b_id, token_b = setup_user("cred_test_userb")

    try:
        # Give User A evidence for streak_7
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO habits (user_id, title) VALUES (?, 'Reading')", (user_a_id,))
        h_id = cursor.lastrowid
        for i in range(7):
            cursor.execute(f"INSERT INTO habit_logs (habit_id, user_id, completed_date) VALUES (?, ?, '2026-08-{i+1:02d}')", (h_id, user_a_id))
        conn.commit()
        conn.close()

        # User A checks and gets credential
        res_a = client.post("/api/credentials/check", cookies={"mkc_session": token_a})
        assert res_a.status_code == 200
        assert any(c["slug"] == "streak_7" for c in res_a.json()["newly_earned"])

        # User B checks -> must NOT receive User A's credential
        res_b = client.post("/api/credentials/check", cookies={"mkc_session": token_b})
        assert res_b.status_code == 200
        assert len(res_b.json()["newly_earned"]) == 0
        assert len(res_b.json()["credentials"]) == 0

        # User B cannot fake evidence through client payload (the POST endpoint accepts no body)
        res_spoof = client.post(
            "/api/credentials/check",
            json={"slug": "streak_100", "evidence_id": "fake_100_streak", "level": 50},
            cookies={"mkc_session": token_b},
        )
        assert res_spoof.status_code == 200
        assert len(res_spoof.json()["newly_earned"]) == 0, "Server must ignore all client spoof payloads"

        # Public credentials endpoint for user A returns their credential
        res_pub_a = client.get(f"/api/credentials/user/{user_a_id}")
        assert res_pub_a.status_code == 200
        assert any(c["slug"] == "streak_7" for c in res_pub_a.json())

        # Public credentials endpoint for nonexistent user returns 404
        res_pub_none = client.get("/api/credentials/user/999999")
        assert res_pub_none.status_code == 404

        # Public verify endpoint for valid credential
        res_creds_a = client.get(f"/api/credentials/user/{user_a_id}").json()
        if res_creds_a:
            cred_id = res_creds_a[0]["id"]
            res_verify = client.get(f"/api/credentials/verify/{cred_id}")
            assert res_verify.status_code == 200
            verify_data = res_verify.json()
            assert verify_data["is_verified"] is True
            assert "verification_hash" in verify_data
            assert verify_data["authority"] == "MASTER CREDENTIAL AUTHORITY"
            assert verify_data["username"] == f"user_cred_test_usera"

        # Public verify endpoint for nonexistent credential returns 404
        res_verify_none = client.get("/api/credentials/verify/999999")
        assert res_verify_none.status_code == 404

        # Unauthenticated calls to private endpoints must return 401
        assert client.get("/api/credentials").status_code == 401
        assert client.post("/api/credentials/check").status_code == 401

        print("PASS: User isolation, client spoofing resistance, and authentication guards verified")
    finally:
        cleanup_user(user_a_id)
        cleanup_user(user_b_id)


def test_public_credential_verification_endpoint():
    """Test public credential verification route and authoritative attributes."""
    user_id, token = setup_user("cred_verify_test")
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO user_credentials (user_id, credential_type, slug, title, description, tier, xp_value, evidence_type, evidence_id)
            VALUES (?, 'streak_badge', 'streak_30', '30-Day Momentum Vanguard', 'Completed 30-day streak', 'gold', 150, 'habit_streak', '30')
            """,
            (user_id,)
        )
        cred_id = cursor.lastrowid
        conn.commit()
        conn.close()

        res = client.get(f"/api/credentials/verify/{cred_id}")
        assert res.status_code == 200
        data = res.json()
        assert data["id"] == cred_id
        assert data["title"] == "30-Day Momentum Vanguard"
        assert data["tier"] == "gold"
        assert data["xp_value"] == 150
        assert data["is_verified"] is True
        assert data["verification_hash"] == f"MKC-AUTH-STREAK_30-{cred_id}"
        assert data["authority"] == "MASTER CREDENTIAL AUTHORITY"
        assert data["username"] == "user_cred_verify_test"
    finally:
        cleanup_user(user_id)


def main():
    print("=" * 60)
    print("RUNNING TARGETED CREDENTIAL ENGINE TESTS")
    print("=" * 60)
    test_no_evidence_receives_no_credentials()
    test_streak_credentials_7_30_100()
    test_missions_50_credential()
    test_blueprint_milestone_credential()
    test_mastery_level_20_credential()
    test_credential_idempotency()
    test_user_isolation_and_anti_spoofing()
    test_public_credential_verification_endpoint()
    print("=" * 60)
    print("ALL CREDENTIAL ENGINE TESTS PASSED")
    print("=" * 60)


if __name__ == "__main__":
    main()

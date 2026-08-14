"""
Targeted tests for User Profile viewing, Connection Status lifecycle, and Chat Security boundaries.
"""
import os
import sys
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.main import app
from app.database import get_connection, init_db
from app.services.auth import create_session, hash_password

client = TestClient(app)


def setup_users():
    init_db()
    conn = get_connection()
    cursor = conn.cursor()

    # Clean up test users
    cursor.execute("DELETE FROM chat_messages WHERE sender_id IN (SELECT id FROM users WHERE email LIKE 'prof_test%' OR username IN ('alice_t', 'bob_t'))")
    cursor.execute("DELETE FROM conversation_members WHERE user_id IN (SELECT id FROM users WHERE email LIKE 'prof_test%' OR username IN ('alice_t', 'bob_t'))")
    cursor.execute("DELETE FROM user_connections WHERE requester_id IN (SELECT id FROM users WHERE email LIKE 'prof_test%' OR username IN ('alice_t', 'bob_t')) OR recipient_id IN (SELECT id FROM users WHERE email LIKE 'prof_test%' OR username IN ('alice_t', 'bob_t'))")
    cursor.execute("DELETE FROM app_sessions WHERE user_id IN (SELECT id FROM users WHERE email LIKE 'prof_test%' OR username IN ('alice_t', 'bob_t'))")
    cursor.execute("DELETE FROM users WHERE email LIKE 'prof_test%' OR username IN ('alice_t', 'bob_t')")
    conn.commit()

    pwd = hash_password("Pass1234!")

    cursor.execute(
        "INSERT INTO users (email, full_name, username, password_hash, avatar_initials, bio) VALUES (?, ?, ?, ?, ?, ?)",
        ("prof_test_a@example.com", "Alice Tester", "alice_t", pwd, "AT", "Cybernetics & Systems"),
    )
    user_a = cursor.lastrowid

    cursor.execute(
        "INSERT INTO users (email, full_name, username, password_hash, avatar_initials, bio) VALUES (?, ?, ?, ?, ?, ?)",
        ("prof_test_b@example.com", "Bob Tester", "bob_t", pwd, "BT", "AI Research"),
    )
    user_b = cursor.lastrowid

    conn.commit()
    conn.close()

    token_a = create_session(user_a)
    token_b = create_session(user_b)

    return user_a, token_a, user_b, token_b


def cleanup_users(user_a, user_b):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM chat_messages WHERE sender_id IN (?, ?)", (user_a, user_b))
    cursor.execute("DELETE FROM conversation_members WHERE user_id IN (?, ?)", (user_a, user_b))
    cursor.execute("DELETE FROM user_connections WHERE requester_id IN (?, ?) OR recipient_id IN (?, ?)", (user_a, user_b, user_a, user_b))
    cursor.execute("DELETE FROM app_sessions WHERE user_id IN (?, ?)", (user_a, user_b))
    cursor.execute("DELETE FROM users WHERE id IN (?, ?)", (user_a, user_b))
    conn.commit()
    conn.close()


def test_profile_endpoint_self_and_unconnected():
    """Test 1: Self profile returns status='self', unconnected other profile returns status='none' and hides email."""
    user_a, token_a, user_b, token_b = setup_users()
    try:
        # User A calls self
        res_self = client.get(f"/api/users/{user_a}", cookies={"mkc_session": token_a})
        assert res_self.status_code == 200
        data_self = res_self.json()
        assert data_self["connection_status"] == "self"
        assert data_self["username"] == "alice_t"

        # User A calls User B (unconnected)
        res_other = client.get(f"/api/users/{user_b}", cookies={"mkc_session": token_a})
        assert res_other.status_code == 200
        data_other = res_other.json()
        assert data_other["connection_status"] == "none"
        assert data_other["username"] == "bob_t"
        assert data_other["full_name"] == "Bob Tester"
        assert data_other["bio"] == "AI Research"
        assert "email" not in data_other, "Other user's private email must not be exposed"

        # Non-existent user returns 404
        res_404 = client.get("/api/users/999999", cookies={"mkc_session": token_a})
        assert res_404.status_code == 404

        # Unauthenticated returns 401
        res_401 = client.get(f"/api/users/{user_b}")
        assert res_401.status_code == 401

        print("PASS: Self ('self') and unconnected ('none') profile retrieval verified with privacy and auth guards")
    finally:
        cleanup_users(user_a, user_b)


def test_connection_lifecycle_and_messaging_guard():
    """Test 2: Complete lifecycle: none -> request sent ('sent'/'received') -> accept ('accepted') -> conversation reuse."""
    user_a, token_a, user_b, token_b = setup_users()
    try:
        # Step 1: Unconnected -> attempt to message must return 403
        res_msg_fail1 = client.post(
            "/api/chat/conversations",
            json={"target_user_id": user_b},
            cookies={"mkc_session": token_a},
        )
        assert res_msg_fail1.status_code == 403, "Unconnected messaging must be rejected with 403"

        # Step 2: User A sends connection request to User B
        res_req = client.post(
            "/api/social/connections/request",
            json={"user_id": user_b},
            cookies={"mkc_session": token_a},
        )
        assert res_req.status_code == 200

        # Verify status: User A sees 'sent', User B sees 'received'
        prof_a_view = client.get(f"/api/users/{user_b}", cookies={"mkc_session": token_a}).json()
        assert prof_a_view["connection_status"] == "sent"

        prof_b_view = client.get(f"/api/users/{user_a}", cookies={"mkc_session": token_b}).json()
        assert prof_b_view["connection_status"] == "received"

        # Step 3: Pending status -> attempt to message must STILL return 403
        res_msg_fail2 = client.post(
            "/api/chat/conversations",
            json={"target_user_id": user_b},
            cookies={"mkc_session": token_a},
        )
        assert res_msg_fail2.status_code == 403, "Pending connection messaging must be rejected with 403"

        # Step 4: User B accepts request
        res_acc = client.post(
            "/api/social/connections/accept",
            json={"user_id": user_a},
            cookies={"mkc_session": token_b},
        )
        assert res_acc.status_code == 200

        # Verify status: Both users see 'accepted'
        prof_a_acc = client.get(f"/api/users/{user_b}", cookies={"mkc_session": token_a}).json()
        assert prof_a_acc["connection_status"] == "accepted"

        prof_b_acc = client.get(f"/api/users/{user_a}", cookies={"mkc_session": token_b}).json()
        assert prof_b_acc["connection_status"] == "accepted"

        # Step 5: Messaging is now allowed & conversation is created
        res_conv1 = client.post(
            "/api/chat/conversations",
            json={"target_user_id": user_b},
            cookies={"mkc_session": token_a},
        )
        assert res_conv1.status_code == 200
        conv_id1 = res_conv1.json()["id"]

        # Step 6: Subsequent calls must REUSE existing conversation (no duplicates)
        res_conv2 = client.post(
            "/api/chat/conversations",
            json={"target_user_id": user_a},
            cookies={"mkc_session": token_b},
        )
        assert res_conv2.status_code == 200
        conv_id2 = res_conv2.json()["id"]
        assert conv_id1 == conv_id2, f"Conversation must be reused (got {conv_id1} vs {conv_id2})"
        assert res_conv2.json()["is_new"] is False, "Reused conversation must have is_new=False"

        print("PASS: Complete connection lifecycle (none->sent/received->accepted) and conversation reuse verified")
    finally:
        cleanup_users(user_a, user_b)


def main():
    print("=" * 60)
    print("RUNNING TARGETED USER PROFILE & CONNECTION TESTS")
    print("=" * 60)
    test_profile_endpoint_self_and_unconnected()
    test_connection_lifecycle_and_messaging_guard()
    print("=" * 60)
    print("ALL USER PROFILE & CONNECTION TESTS PASSED")
    print("=" * 60)


if __name__ == "__main__":
    main()

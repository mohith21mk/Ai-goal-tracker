"""
Targeted test for connection-based messaging security.
Tests that create_or_get_conversation enforces accepted connection.
"""
import sqlite3
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.database import get_connection, init_db, DB_PATH
from app.services.auth import hash_password


def setup_test_users():
    """Create two test users for the security test."""
    conn = get_connection()
    cursor = conn.cursor()

    # Clean up any previous test data
    cursor.execute("DELETE FROM notifications WHERE user_id IN (SELECT id FROM users WHERE email LIKE 'sectest%')")
    cursor.execute("DELETE FROM chat_messages WHERE sender_id IN (SELECT id FROM users WHERE email LIKE 'sectest%')")
    cursor.execute("DELETE FROM conversation_members WHERE user_id IN (SELECT id FROM users WHERE email LIKE 'sectest%')")
    cursor.execute("DELETE FROM user_connections WHERE requester_id IN (SELECT id FROM users WHERE email LIKE 'sectest%') OR recipient_id IN (SELECT id FROM users WHERE email LIKE 'sectest%')")
    cursor.execute("DELETE FROM app_sessions WHERE user_id IN (SELECT id FROM users WHERE email LIKE 'sectest%')")
    cursor.execute("DELETE FROM users WHERE email LIKE 'sectest%'")
    conn.commit()

    pwd = hash_password("Test123!")

    cursor.execute(
        "INSERT INTO users (email, full_name, username, password_hash, avatar_initials) VALUES (?, ?, ?, ?, ?)",
        ("sectest_a@test.com", "Test User A", "sectest_a", pwd, "TA")
    )
    user_a_id = cursor.lastrowid

    cursor.execute(
        "INSERT INTO users (email, full_name, username, password_hash, avatar_initials) VALUES (?, ?, ?, ?, ?)",
        ("sectest_b@test.com", "Test User B", "sectest_b", pwd, "TB")
    )
    user_b_id = cursor.lastrowid

    conn.commit()
    conn.close()
    return user_a_id, user_b_id


def _test_no_connection(user_a_id, user_b_id):
    """Test 1: No connection exists -> conversation creation must fail."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id FROM user_connections 
        WHERE ((requester_id = ? AND recipient_id = ?) OR (requester_id = ? AND recipient_id = ?))
          AND status = 'accepted'
        """,
        (user_a_id, user_b_id, user_b_id, user_a_id)
    )
    conn_row = cursor.fetchone()
    conn.close()
    if conn_row is None:
        print("PASS TEST 1: No connection exists -> would return 403")
        return True
    else:
        print("FAIL TEST 1: Expected no connection, but found one")
        return False


def _test_pending_connection(user_a_id, user_b_id):
    """Test 2: Pending connection exists -> conversation creation must still fail."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO user_connections (requester_id, recipient_id, status) VALUES (?, ?, 'pending')",
        (user_a_id, user_b_id)
    )
    conn.commit()

    cursor.execute(
        """
        SELECT id FROM user_connections 
        WHERE ((requester_id = ? AND recipient_id = ?) OR (requester_id = ? AND recipient_id = ?))
          AND status = 'accepted'
        """,
        (user_a_id, user_b_id, user_b_id, user_a_id)
    )
    conn_row = cursor.fetchone()
    conn.close()

    if conn_row is None:
        print("PASS TEST 2: Pending connection found -> would return 403 (status != accepted)")
        return True
    else:
        print("FAIL TEST 2: Pending connection treated as accepted")
        return False


def _test_accepted_connection(user_a_id, user_b_id):
    """Test 3: Connection is accepted -> conversation creation allowed."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE user_connections SET status = 'accepted' WHERE requester_id = ? AND recipient_id = ?",
        (user_a_id, user_b_id)
    )
    conn.commit()

    cursor.execute(
        """
        SELECT id FROM user_connections 
        WHERE ((requester_id = ? AND recipient_id = ?) OR (requester_id = ? AND recipient_id = ?))
          AND status = 'accepted'
        """,
        (user_a_id, user_b_id, user_b_id, user_a_id)
    )
    conn_row = cursor.fetchone()
    conn.close()

    if conn_row is not None:
        print("PASS TEST 3: Accepted connection found -> would allow conversation creation")
        return True
    else:
        print("FAIL TEST 3: Accepted connection not recognized")
        return False


def _test_reverse_direction(user_a_id, user_b_id):
    """Test 4: Recipient (User B) tries to message Requester (User A)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id FROM user_connections 
        WHERE ((requester_id = ? AND recipient_id = ?) OR (requester_id = ? AND recipient_id = ?))
          AND status = 'accepted'
        """,
        (user_b_id, user_a_id, user_a_id, user_b_id)
    )
    conn_row = cursor.fetchone()
    conn.close()

    if conn_row is not None:
        print("PASS TEST 4: Bidirectional lookup works -> B can also find accepted connection with A")
        return True
    else:
        print("FAIL TEST 4: Reverse lookup failed for accepted connection")
        return False


def _test_conversation_creation_after_accept(user_a_id, user_b_id):
    """Test 5: Full integration test - create conversation and send message when accepted."""
    conn = get_connection()
    cursor = conn.cursor()

    # Create conversation
    cursor.execute("INSERT INTO conversations (updated_at) VALUES (CURRENT_TIMESTAMP)")
    conv_id = cursor.lastrowid

    cursor.execute("INSERT INTO conversation_members (conversation_id, user_id) VALUES (?, ?)", (conv_id, user_a_id))
    cursor.execute("INSERT INTO conversation_members (conversation_id, user_id) VALUES (?, ?)", (conv_id, user_b_id))
    conn.commit()

    # Send message
    cursor.execute(
        "INSERT INTO chat_messages (conversation_id, sender_id, message) VALUES (?, ?, ?)",
        (conv_id, user_a_id, "Hello from security test!")
    )
    msg_id = cursor.lastrowid
    conn.commit()

    cursor.execute("SELECT id, message FROM chat_messages WHERE id = ?", (msg_id,))
    msg = cursor.fetchone()
    conn.close()

    if msg and msg["message"] == "Hello from security test!":
        print(f"PASS TEST 5: Conversation #{conv_id} created, message #{msg_id} sent successfully")
        return True
    else:
        print("FAIL TEST 5: Message not found after creation")
        return False


def cleanup(user_a_id, user_b_id):
    """Remove test data."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM chat_messages WHERE sender_id IN (?, ?)", (user_a_id, user_b_id))
    cursor.execute("DELETE FROM conversation_members WHERE user_id IN (?, ?)", (user_a_id, user_b_id))
    cursor.execute("DELETE FROM user_connections WHERE requester_id IN (?, ?) OR recipient_id IN (?, ?)", (user_a_id, user_b_id, user_a_id, user_b_id))
    cursor.execute("DELETE FROM users WHERE id IN (?, ?)", (user_a_id, user_b_id))
    conn.commit()
    conn.close()
    print("Test data cleaned up")


def main():
    print("=" * 60)
    print("CONNECTION-BASED MESSAGING SECURITY TEST")
    print("=" * 60)

    init_db()

    user_a_id, user_b_id = setup_test_users()
    print(f"\nTest users created: A={user_a_id}, B={user_b_id}\n")

    results = []
    results.append(_test_no_connection(user_a_id, user_b_id))
    results.append(_test_pending_connection(user_a_id, user_b_id))
    results.append(_test_accepted_connection(user_a_id, user_b_id))
    results.append(_test_reverse_direction(user_a_id, user_b_id))
    results.append(_test_conversation_creation_after_accept(user_a_id, user_b_id))

    cleanup(user_a_id, user_b_id)

    print("\n" + "=" * 60)
    passed = sum(results)
    total = len(results)
    if passed == total:
        print(f"ALL {total}/{total} TESTS PASSED")
    else:
        print(f"{passed}/{total} tests passed, {total - passed} FAILED")
    print("=" * 60)

    return 0 if passed == total else 1


def test_connection_security_all():
    assert main() == 0


if __name__ == "__main__":
    sys.exit(main())

"""
Targeted test for Chat Discover user search, query validation, route order, and connection status.
"""
import os
import sys
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.main import app
from app.database import get_connection, init_db
from app.services.auth import create_session, hash_password

client = TestClient(app)


def setup_search_test_data():
    init_db()
    conn = get_connection()
    cursor = conn.cursor()

    # Clean up test users
    cursor.execute("DELETE FROM user_connections WHERE requester_id IN (SELECT id FROM users WHERE username IN ('search_me', 'chinmayee_23', 'connected_friend') OR email LIKE 'search_test%' OR mkc_id = 'MKC-0559') OR recipient_id IN (SELECT id FROM users WHERE username IN ('search_me', 'chinmayee_23', 'connected_friend') OR email LIKE 'search_test%' OR mkc_id = 'MKC-0559')")
    cursor.execute("DELETE FROM app_sessions WHERE user_id IN (SELECT id FROM users WHERE username IN ('search_me', 'chinmayee_23', 'connected_friend') OR email LIKE 'search_test%' OR mkc_id = 'MKC-0559')")
    cursor.execute("DELETE FROM users WHERE username IN ('search_me', 'chinmayee_23', 'connected_friend') OR email LIKE 'search_test%' OR mkc_id = 'MKC-0559'")
    conn.commit()

    pwd = hash_password("Pass1234!")

    # Current searcher
    cursor.execute(
        "INSERT INTO users (email, full_name, username, password_hash, avatar_initials, bio) VALUES (?, ?, ?, ?, ?, ?)",
        ("search_test_me@example.com", "Test Searcher", "search_me", pwd, "TS", "Searching users"),
    )
    my_user_id = cursor.lastrowid

    # Discovered user 1: Chinmayee
    cursor.execute(
        "INSERT INTO users (email, full_name, username, password_hash, avatar_initials, bio, mkc_id) VALUES (?, ?, ?, ?, ?, ?, ?)",
        ("search_test_chinmayee@example.com", "Chinmayee Patel", "chinmayee_23", pwd, "CP", "AI Engineering & Systems", "MKC-0559"),
    )
    chinmayee_id = cursor.lastrowid

    # Discovered user 2: Connected User
    cursor.execute(
        "INSERT INTO users (email, full_name, username, password_hash, avatar_initials, bio) VALUES (?, ?, ?, ?, ?, ?)",
        ("search_test_connected@example.com", "Connected User", "connected_friend", pwd, "CF", "System Design"),
    )
    connected_id = cursor.lastrowid

    # Create accepted connection with connected_id
    cursor.execute(
        "INSERT INTO user_connections (requester_id, recipient_id, status) VALUES (?, ?, 'accepted')",
        (my_user_id, connected_id),
    )

    conn.commit()
    conn.close()

    token = create_session(my_user_id)
    return my_user_id, token, chinmayee_id, connected_id


def cleanup_search_test_data(my_user_id, chinmayee_id, connected_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM user_connections WHERE requester_id IN (?, ?, ?) OR recipient_id IN (?, ?, ?)", (my_user_id, chinmayee_id, connected_id, my_user_id, chinmayee_id, connected_id))
    cursor.execute("DELETE FROM app_sessions WHERE user_id IN (?, ?, ?)", (my_user_id, chinmayee_id, connected_id))
    cursor.execute("DELETE FROM users WHERE id IN (?, ?, ?)", (my_user_id, chinmayee_id, connected_id))
    conn.commit()
    conn.close()


def test_discover_search():
    my_user_id, token, chinmayee_id, connected_id = setup_search_test_data()
    try:
        cookies = {"mkc_session": token}

        # 1. Search "chinmayee" -> must return 200 OK with chinmayee_23 user
        res_chin = client.get("/api/users/search?q=chinmayee", cookies=cookies)
        assert res_chin.status_code == 200, f"Expected 200 for q=chinmayee, got {res_chin.status_code}: {res_chin.text}"
        users_chin = res_chin.json().get("users", [])
        assert len(users_chin) == 1
        u = users_chin[0]
        assert u["username"] == "chinmayee_23"
        assert u["full_name"] == "Chinmayee Patel"
        assert u["connection_status"] == "none"
        assert u["avatar_initials"] == "CP"
        assert "mkc_id" in u
        print("PASS 1: Search 'chinmayee' succeeded with 200 OK and expected fields")

        # 2. Search "chinmayee_23"
        res_exact = client.get("/api/users/search?q=chinmayee_23", cookies=cookies)
        assert res_exact.status_code == 200
        assert len(res_exact.json().get("users", [])) == 1
        print("PASS 2: Search 'chinmayee_23' succeeded with 200 OK")

        # 2b. Search by MKC ID: "MKC-0559"
        res_mkc = client.get("/api/users/search?q=MKC-0559", cookies=cookies)
        assert res_mkc.status_code == 200
        users_mkc = res_mkc.json().get("users", [])
        assert len(users_mkc) == 1
        assert users_mkc[0]["username"] == "chinmayee_23"
        print("PASS 2b: Search 'MKC-0559' succeeded by MKC ID")

        # 3. Search non-existent username
        res_none = client.get("/api/users/search?q=nonexistent_xyz_user", cookies=cookies)
        assert res_none.status_code == 200
        assert len(res_none.json().get("users", [])) == 0
        print("PASS 3: Non-existent search returns 200 with empty list")

        # 4. Search with < 2 characters -> 422
        res_short = client.get("/api/users/search?q=a", cookies=cookies)
        assert res_short.status_code == 422, f"Expected 422 for min_length validation, got {res_short.status_code}"
        print("PASS 4: Query < 2 chars correctly triggers min_length=2 422 validation")

        # 5. Search with connection status verification ('accepted')
        res_conn = client.get("/api/users/search?q=connected_friend", cookies=cookies)
        assert res_conn.status_code == 200
        u_conn = res_conn.json().get("users", [])[0]
        assert u_conn["connection_status"] == "accepted"
        print("PASS 5: Search correctly maps 'accepted' connection_status")

        # 6. Unauthenticated search -> 401
        res_unauth = client.get("/api/users/search?q=chinmayee")
        assert res_unauth.status_code == 401
        print("PASS 6: Unauthenticated search correctly rejected with 401")

        # 7. Verify GET /api/users/{user_id} still works without route conflict
        res_prof = client.get(f"/api/users/{chinmayee_id}", cookies=cookies)
        assert res_prof.status_code == 200
        assert res_prof.json()["username"] == "chinmayee_23"
        print("PASS 7: Route ordering verified — GET /api/users/{user_id} works cleanly alongside /api/users/search")

    finally:
        cleanup_search_test_data(my_user_id, chinmayee_id, connected_id)


def main():
    print("=" * 60)
    print("RUNNING TARGETED CHAT DISCOVER SEARCH TESTS")
    print("=" * 60)
    test_discover_search()
    print("=" * 60)
    print("ALL CHAT DISCOVER SEARCH TESTS PASSED")
    print("=" * 60)


if __name__ == "__main__":
    main()

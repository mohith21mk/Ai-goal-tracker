import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from app import create_app
from app.database import get_connection
from app.services.auth import hash_password, create_session

app = create_app()
client = TestClient(app)


@pytest.fixture(scope="module")
def setup_three_users():
    conn = get_connection()
    cursor = conn.cursor()

    # Clean up any leftover test accounts
    cursor.execute("DELETE FROM users WHERE email IN ('uni_user_a@mkc.test', 'uni_user_b@mkc.test', 'uni_user_c@mkc.test', 'uni_deact@mkc.test')")
    conn.commit()

    # User A
    cursor.execute(
        """
        INSERT INTO users (email, username, password_hash, full_name, mkc_id, email_verified, onboarding_completed)
        VALUES ('uni_user_a@mkc.test', 'uni_user_a', ?, 'Alpha Tester', 'MKC-UNI-A', 1, 1)
        """,
        (hash_password("PasswordAlpha123!"),)
    )
    user_a_id = cursor.lastrowid

    # User B
    cursor.execute(
        """
        INSERT INTO users (email, username, password_hash, full_name, mkc_id, email_verified, onboarding_completed)
        VALUES ('uni_user_b@mkc.test', 'uni_user_b', ?, 'Beta Builder', 'MKC-UNI-B', 1, 1)
        """,
        (hash_password("PasswordBeta123!"),)
    )
    user_b_id = cursor.lastrowid

    # User C
    cursor.execute(
        """
        INSERT INTO users (email, username, password_hash, full_name, mkc_id, email_verified, onboarding_completed)
        VALUES ('uni_user_c@mkc.test', 'uni_user_c', ?, 'Charlie Coach', 'MKC-UNI-C', 1, 1)
        """,
        (hash_password("PasswordCharlie123!"),)
    )
    user_c_id = cursor.lastrowid

    # Deactivated User
    cursor.execute(
        """
        INSERT INTO users (email, username, password_hash, full_name, mkc_id, email_verified, onboarding_completed, deactivated_at)
        VALUES ('uni_deact@mkc.test', 'uni_deact_user', ?, 'Deactivated User', 'MKC-UNI-D', 1, 1, '2026-01-01 00:00:00')
        """,
        (hash_password("PasswordDeact123!"),)
    )
    deact_id = cursor.lastrowid

    conn.commit()
    conn.close()

    session_a = create_session(user_a_id)
    session_b = create_session(user_b_id)
    session_c = create_session(user_c_id)

    yield {
        "user_a": {"id": user_a_id, "token": session_a, "email": "uni_user_a@mkc.test", "username": "uni_user_a"},
        "user_b": {"id": user_b_id, "token": session_b, "email": "uni_user_b@mkc.test", "username": "uni_user_b"},
        "user_c": {"id": user_c_id, "token": session_c, "email": "uni_user_c@mkc.test", "username": "uni_user_c"},
        "deact": {"id": deact_id},
    }

    # Teardown
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE id IN (?, ?, ?, ?)", (user_a_id, user_b_id, user_c_id, deact_id))
    cursor.execute("DELETE FROM user_connections WHERE requester_id IN (?, ?, ?) OR recipient_id IN (?, ?, ?)",
                   (user_a_id, user_b_id, user_c_id, user_a_id, user_b_id, user_c_id))
    cursor.execute("DELETE FROM notifications WHERE user_id IN (?, ?, ?)", (user_a_id, user_b_id, user_c_id))
    conn.commit()
    conn.close()


def test_auth_login_switch_and_me(setup_three_users):
    user_a = setup_three_users["user_a"]
    user_b = setup_three_users["user_b"]

    # 1. Login User A
    res_a = client.post("/api/auth/login", json={"identifier": user_a["email"], "password": "PasswordAlpha123!"})
    assert res_a.status_code == 200
    token_a = res_a.cookies.get("mkc_session")
    assert token_a is not None

    # Check /me for User A
    res_me_a = client.get("/api/auth/me", cookies={"mkc_session": token_a})
    assert res_me_a.status_code == 200
    assert res_me_a.json()["id"] == user_a["id"]
    assert res_me_a.json()["username"] == "uni_user_a"

    # 2. Logout User A
    res_logout = client.post("/api/auth/logout", cookies={"mkc_session": token_a})
    assert res_logout.status_code == 200

    # Verify token_a is invalidated
    res_me_invalid = client.get("/api/auth/me", cookies={"mkc_session": token_a})
    assert res_me_invalid.status_code == 401

    # 3. Login User B
    res_b = client.post("/api/auth/login", json={"identifier": user_b["email"], "password": "PasswordBeta123!"})
    assert res_b.status_code == 200
    token_b = res_b.cookies.get("mkc_session")

    res_me_b = client.get("/api/auth/me", cookies={"mkc_session": token_b})
    assert res_me_b.status_code == 200
    assert res_me_b.json()["id"] == user_b["id"]
    assert res_me_b.json()["username"] == "uni_user_b"


def test_user_discovery_and_search_isolation(setup_three_users):
    user_a = setup_three_users["user_a"]
    user_b = setup_three_users["user_b"]
    user_c = setup_three_users["user_c"]
    deact = setup_three_users["deact"]

    # 1. User A searches with empty query -> returns other users, excludes User A and deactivated users
    res = client.get("/api/users/search", cookies={"mkc_session": user_a["token"]})
    assert res.status_code == 200
    users = res.json()["users"]
    user_ids = [u["id"] for u in users]

    assert user_a["id"] not in user_ids, "User A must not appear in own search results"
    assert user_b["id"] in user_ids, "User B should be discoverable"
    assert user_c["id"] in user_ids, "User C should be discoverable"
    assert deact["id"] not in user_ids, "Deactivated user must be excluded"

    # 2. User A searches by username query "beta"
    res_query = client.get("/api/users/search?q=beta", cookies={"mkc_session": user_a["token"]})
    assert res_query.status_code == 200
    matched = res_query.json()["users"]
    assert len(matched) >= 1
    assert any(u["username"] == "uni_user_b" for u in matched)

    # 3. User B searches by query "alpha"
    res_b_search = client.get("/api/users/search?q=alpha", cookies={"mkc_session": user_b["token"]})
    assert res_b_search.status_code == 200
    assert any(u["username"] == "uni_user_a" for u in res_b_search.json()["users"])


def test_connections_and_notifications_lifecycle(setup_three_users):
    user_a = setup_three_users["user_a"]
    user_b = setup_three_users["user_b"]
    user_c = setup_three_users["user_c"]

    # 1. User A tries to connect to self -> 400
    res = client.post("/api/social/connections/request", json={"user_id": user_a["id"]}, cookies={"mkc_session": user_a["token"]})
    assert res.status_code == 400

    # 2. User A sends connection request to User B
    res_req = client.post("/api/social/connections/request", json={"user_id": user_b["id"]}, cookies={"mkc_session": user_a["token"]})
    assert res_req.status_code == 200

    # Duplicate request -> 400
    res_dup = client.post("/api/social/connections/request", json={"user_id": user_b["id"]}, cookies={"mkc_session": user_a["token"]})
    assert res_dup.status_code == 400

    # 3. User B sees pending received request
    res_conns_b = client.get("/api/social/connections", cookies={"mkc_session": user_b["token"]})
    assert res_conns_b.status_code == 200
    pending_b = res_conns_b.json()["pending_received"]
    assert any(p["id"] == user_a["id"] for p in pending_b)

    # 4. User B checks notifications -> sees Connection Request notification
    res_notifs_b = client.get("/api/notifications", cookies={"mkc_session": user_b["token"]})
    assert res_notifs_b.status_code == 200
    notifs_b = res_notifs_b.json()
    assert any(n["type"] == "connection_request" for n in notifs_b)

    # User A does NOT have this notification
    res_notifs_a = client.get("/api/notifications", cookies={"mkc_session": user_a["token"]})
    assert not any(n["type"] == "connection_request" and n["reference_id"] == user_a["id"] for n in res_notifs_a.json())

    # 5. User C tries to accept A's request to B -> 400 (not requested from C)
    res_c_hack = client.post("/api/social/connections/accept", json={"user_id": user_a["id"]}, cookies={"mkc_session": user_c["token"]})
    assert res_c_hack.status_code == 400

    # 6. User B accepts User A's connection
    res_accept = client.post("/api/social/connections/accept", json={"user_id": user_a["id"]}, cookies={"mkc_session": user_b["token"]})
    assert res_accept.status_code == 200

    # 7. Both users now see status 'accepted'
    res_conns_a = client.get("/api/social/connections", cookies={"mkc_session": user_a["token"]})
    assert any(c["id"] == user_b["id"] for c in res_conns_a.json()["accepted"])


def test_messaging_between_connected_users_and_third_party_isolation(setup_three_users):
    user_a = setup_three_users["user_a"]
    user_b = setup_three_users["user_b"]
    user_c = setup_three_users["user_c"]

    # 1. User A tries to create conversation with unconnected User C -> 403 Forbidden
    res_unconnected = client.post(
        "/api/chat/conversations",
        json={"target_user_id": user_c["id"]},
        cookies={"mkc_session": user_a["token"]}
    )
    assert res_unconnected.status_code == 403

    # 2. User A starts conversation with connected User B -> 200 OK
    res_conv = client.post(
        "/api/chat/conversations",
        json={"target_user_id": user_b["id"]},
        cookies={"mkc_session": user_a["token"]}
    )
    assert res_conv.status_code == 200
    conv_id = res_conv.json()["id"]

    # Insert a message from User A to User B directly into chat_messages
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO chat_messages (conversation_id, sender_id, message) VALUES (?, ?, ?)",
        (conv_id, user_a["id"], "Secret message from Alpha to Beta")
    )
    msg_id = cursor.lastrowid
    conn.commit()
    conn.close()

    # 3. User B fetches messages -> sees Alpha's message
    res_b_msgs = client.get(f"/api/chat/conversations/{conv_id}/messages", cookies={"mkc_session": user_b["token"]})
    assert res_b_msgs.status_code == 200
    msgs = res_b_msgs.json()
    assert len(msgs) >= 1
    assert any(m["content"] == "Secret message from Alpha to Beta" for m in msgs)

    # 4. User C (third party) tries to fetch conversation messages -> 403 Forbidden
    res_c_spy = client.get(f"/api/chat/conversations/{conv_id}/messages", cookies={"mkc_session": user_c["token"]})
    assert res_c_spy.status_code == 403

    # 5. User B tries to delete User A's message -> 403 Forbidden
    res_del_hack = client.delete(f"/api/chat/messages/{msg_id}", cookies={"mkc_session": user_b["token"]})
    assert res_del_hack.status_code == 403

    # 6. User A deletes own message -> 200 OK
    res_del_ok = client.delete(f"/api/chat/messages/{msg_id}", cookies={"mkc_session": user_a["token"]})
    assert res_del_ok.status_code == 200


def test_community_post_interactions_and_credential_protection(setup_three_users):
    user_a = setup_three_users["user_a"]
    user_b = setup_three_users["user_b"]
    user_c = setup_three_users["user_c"]

    # 1. User A creates a post
    res_post = client.post(
        "/api/community/posts",
        json={"content": "Community message by Alpha", "category": "wins"},
        cookies={"mkc_session": user_a["token"]}
    )
    assert res_post.status_code == 200
    post_id = res_post.json()["id"]

    # 2. User B and User C view feed -> see Alpha's post
    res_feed = client.get("/api/community/posts", cookies={"mkc_session": user_b["token"]})
    assert res_feed.status_code == 200
    assert any(p["id"] == post_id for p in res_feed.json())

    # 3. User B likes the post
    res_like = client.post(f"/api/community/posts/{post_id}/like", cookies={"mkc_session": user_b["token"]})
    assert res_like.status_code == 200
    assert res_like.json()["likes_count"] >= 1
    assert res_like.json()["user_has_liked"] is True

    # 4. User C cannot edit or delete User A's post -> 403
    res_edit_c = client.patch(f"/api/community/posts/{post_id}", json={"content": "Hacked"}, cookies={"mkc_session": user_c["token"]})
    assert res_edit_c.status_code == 403

    res_del_c = client.delete(f"/api/community/posts/{post_id}", cookies={"mkc_session": user_c["token"]})
    assert res_del_c.status_code == 403

    # 5. User A deletes own post -> 200
    res_del_a = client.delete(f"/api/community/posts/{post_id}", cookies={"mkc_session": user_a["token"]})
    assert res_del_a.status_code == 200


def test_liveness_and_readiness_endpoints():
    # Liveness
    res_live = client.get("/health")
    assert res_live.status_code == 200
    assert res_live.json()["status"] == "LIVE"

    # Readiness
    res_ready = client.get("/ready")
    assert res_ready.status_code in (200, 503)
    assert "checks" in res_ready.json()
    assert "database" in res_ready.json()["checks"]

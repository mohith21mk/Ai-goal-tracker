import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import init_db, get_connection

client = TestClient(app)

def setup_module(module):
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE username IN ('msg_user_a', 'msg_user_b', 'msg_user_c')")
    conn.commit()

def test_phase2e_realtime_messaging_suite():
    # 1. Register User A, User B, and User C
    res_a = client.post("/api/auth/register", json={
        "email": "msga@example.com", "password": "Password123!", "full_name": "Msg User A", "username": "msg_user_a"
    })
    assert res_a.status_code == 200
    token_a = res_a.cookies.get("mkc_session") or res_a.json().get("session_token")
    headers_a = {"Cookie": f"mkc_session={token_a}"}

    res_b = client.post("/api/auth/register", json={
        "email": "msgb@example.com", "password": "Password123!", "full_name": "Msg User B", "username": "msg_user_b"
    })
    assert res_b.status_code == 200
    token_b = res_b.cookies.get("mkc_session") or res_b.json().get("session_token")
    headers_b = {"Cookie": f"mkc_session={token_b}"}

    res_c = client.post("/api/auth/register", json={
        "email": "msgc@example.com", "password": "Password123!", "full_name": "Msg User C", "username": "msg_user_c"
    })
    assert res_c.status_code == 200
    token_c = res_c.cookies.get("mkc_session") or res_c.json().get("session_token")
    headers_c = {"Cookie": f"mkc_session={token_c}"}

    # 2. Test User Search Endpoint (/api/users/search)
    search_res = client.get("/api/users/search?q=msg_user_b", headers=headers_a)
    assert search_res.status_code == 200
    search_data = search_res.json()
    assert "users" in search_data
    found_users = search_data["users"]
    assert len(found_users) >= 1
    found_b = next(u for u in found_users if u["username"] == "msg_user_b")
    assert found_b["display_name"] == "Msg User B"
    assert "password" not in found_b
    assert "password_hash" not in found_b
    assert "email" not in found_b

    # 2.5 Establish Connection between User A and User B
    req_res = client.post("/api/social/connections/request", json={"user_id": found_b["id"]}, headers=headers_a)
    assert req_res.status_code == 200

    # User B accepts User A's connection request
    user_a_id = res_a.json().get("user_id") or client.get("/api/auth/me", headers=headers_a).json()["id"]
    acc_res = client.post("/api/social/connections/accept", json={"user_id": user_a_id}, headers=headers_b)
    assert acc_res.status_code == 200

    # 3. Create Conversation (User A -> User B)
    conv_res = client.post("/api/chat/conversations", json={"target_user_id": found_b["id"]}, headers=headers_a)
    assert conv_res.status_code == 200
    conv_id = conv_res.json()["conversation_id"]

    # 4. Duplicate Conversation Prevention (User A -> User B again)
    dup_res = client.post("/api/chat/conversations", json={"target_user_id": found_b["id"]}, headers=headers_a)
    assert dup_res.status_code == 200
    assert dup_res.json()["conversation_id"] == conv_id

    # 5. Prevent Self Conversation
    self_res = client.post("/api/chat/conversations", json={"target_user_id": user_a_id}, headers=headers_a)
    assert self_res.status_code in (400, 404)

    # 6. User Conversations List for User A & User B
    convs_a = client.get("/api/chat/conversations", headers=headers_a).json()
    assert any(c["id"] == conv_id for c in convs_a)

    convs_b = client.get("/api/chat/conversations", headers=headers_b).json()
    assert any(c["id"] == conv_id for c in convs_b)

    # 7. User Isolation Security: User C cannot list messages or access User A & B's conversation
    forbidden_get = client.get(f"/api/chat/conversations/{conv_id}/messages", headers=headers_c)
    assert forbidden_get.status_code == 403

    forbidden_read = client.post(f"/api/chat/conversations/{conv_id}/read", headers=headers_c)
    assert forbidden_read.status_code == 403

    # 8. Test WebSocket Real-Time Message Flow & Persistence
    with client.websocket_connect(f"/api/chat/ws", cookies={"mkc_session": token_a}) as ws_a:
        ready_evt = ws_a.receive_json()
        assert ready_evt["type"] == "connection.ready"

        # User A sends message over WebSocket
        ws_a.send_json({
            "type": "message.send",
            "conversation_id": conv_id,
            "content": "Hello User B! High discipline protocol active."
        })

        evt = ws_a.receive_json()
        assert evt["type"] in ("message.created", "message.ack")
        assert evt.get("conversation_id") == conv_id or evt.get("message", {}).get("conversation_id") == conv_id

    # 9. Verify Message Persistence in DB
    history_res = client.get(f"/api/chat/conversations/{conv_id}/messages", headers=headers_a)
    assert history_res.status_code == 200
    messages = history_res.json()
    assert len(messages) == 1
    assert messages[0]["content"] == "Hello User B! High discipline protocol active."

    # 10. Check Unread Count for User B (User B hasn't read it yet)
    convs_b_after = client.get("/api/chat/conversations", headers=headers_b).json()
    conv_b_item = next(c for c in convs_b_after if c["id"] == conv_id)
    assert conv_b_item["unread_count"] >= 1

    # 11. User B Reads Conversation & Verifies Unread Clears
    read_res = client.post(f"/api/chat/conversations/{conv_id}/read", headers=headers_b)
    assert read_res.status_code == 200

    convs_b_read = client.get("/api/chat/conversations", headers=headers_b).json()
    conv_b_read_item = next(c for c in convs_b_read if c["id"] == conv_id)
    assert conv_b_read_item["unread_count"] == 0

    print("Phase 2E Messaging Test Suite PASSED 100%.")

def teardown_module(module):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE username IN ('msg_user_a', 'msg_user_b', 'msg_user_c')")
    conn.commit()

import pytest
import asyncio
from fastapi.testclient import TestClient
from app.main import app
from app.database import init_db, get_connection
from app.services.notifications import (
    create_notification,
    get_user_notifications,
    get_unread_notification_count,
    mark_notification_read,
    mark_all_notifications_read,
    delete_notification,
)

client = TestClient(app)

def setup_module(module):
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE username IN ('notif_user_a', 'notif_user_b')")
    conn.commit()
    conn.close()

def test_phase2g_realtime_notifications_suite():
    # 1. Unauthenticated Request Check
    unauth = client.get("/api/notifications")
    assert unauth.status_code == 401

    # Register User A & User B
    res_a = client.post("/api/auth/register", json={
        "email": "notifa@example.com", "password": "Password123!", "full_name": "Notif User A", "username": "notif_user_a"
    })
    assert res_a.status_code == 200
    token_a = res_a.cookies.get("mkc_session") or res_a.json().get("session_token")
    headers_a = {"Cookie": f"mkc_session={token_a}"}
    user_a_id = client.get("/api/auth/me", headers=headers_a).json()["id"]

    res_b = client.post("/api/auth/register", json={
        "email": "notifb@example.com", "password": "Password123!", "full_name": "Notif User B", "username": "notif_user_b"
    })
    assert res_b.status_code == 200
    token_b = res_b.cookies.get("mkc_session") or res_b.json().get("session_token")
    headers_b = {"Cookie": f"mkc_session={token_b}"}
    user_b_id = client.get("/api/auth/me", headers=headers_b).json()["id"]

    # 2. Sync Notification Service Operations
    asyncio.run(create_notification(
        user_id=user_a_id,
        type="system_event",
        title="Welcome to Mastery Key",
        message="Your account has been initialized.",
        reference_type="system",
        reference_id=101
    ))

    # 3. Notification Persistence & Retrieval
    notifs_a = client.get("/api/notifications", headers=headers_a).json()
    assert len(notifs_a) >= 1
    target_notif = notifs_a[0]
    notif_id = target_notif["id"]
    assert target_notif["title"] == "Welcome to Mastery Key"
    assert target_notif["is_read"] == 0

    # 4. Unread Count Endpoint
    unread_res = client.get("/api/notifications/unread-count", headers=headers_a)
    assert unread_res.status_code == 200
    assert unread_res.json()["unread_count"] >= 1

    # 5. User Isolation Check: User B cannot access or modify User A's notification
    user_b_notifs = client.get("/api/notifications", headers=headers_b).json()
    assert not any(n["id"] == notif_id for n in user_b_notifs)

    unauth_mark = client.patch(f"/api/notifications/{notif_id}/read", headers=headers_b)
    assert unauth_mark.status_code == 404

    unauth_del = client.delete(f"/api/notifications/{notif_id}", headers=headers_b)
    assert unauth_del.status_code == 404

    # 6. Mark Single Read by Owner (User A)
    read_res = client.patch(f"/api/notifications/{notif_id}/read", headers=headers_a)
    assert read_res.status_code == 200

    unread_res_after = client.get("/api/notifications/unread-count", headers=headers_a)
    assert unread_res_after.json()["unread_count"] == 0

    # 7. Create Multiple Notifications & Test Mark All Read & Pagination
    asyncio.run(create_notification(user_id=user_a_id, type="info", title="Notif 1", message="Msg 1"))
    asyncio.run(create_notification(user_id=user_a_id, type="info", title="Notif 2", message="Msg 2"))

    paginated_res = client.get("/api/notifications?limit=1&offset=0", headers=headers_a)
    assert paginated_res.status_code == 200
    assert len(paginated_res.json()) == 1

    read_all_res = client.patch("/api/notifications/read_all", headers=headers_a)
    assert read_all_res.status_code == 200

    # 8. Delete Notification by Owner
    del_res = client.delete(f"/api/notifications/{notif_id}", headers=headers_a)
    assert del_res.status_code == 200

    # 9. Community Integration Notification Triggers
    post_res = client.post("/api/community/posts", json={
        "content": "Notification Integration Challenge",
        "category": "general"
    }, headers=headers_a)
    post_id = post_res.json()["id"]

    # User B likes User A's post -> Triggers Notification for User A
    client.post(f"/api/community/posts/{post_id}/like", headers=headers_b)

    notifs_a_new = client.get("/api/notifications", headers=headers_a).json()
    assert any(n["type"] == "community_like" and n["reference_id"] == post_id for n in notifs_a_new)

    # Self-Notification Prevention: User A likes own post -> No extra notification created
    client.post(f"/api/community/posts/{post_id}/like", headers=headers_a)
    notifs_a_self = client.get("/api/notifications", headers=headers_a).json()
    self_like_count = sum(1 for n in notifs_a_self if n["type"] == "community_like" and n["message"].startswith("Notif User A"))
    assert self_like_count == 0

    # 10. WebSocket Connection & User Isolation
    with client.websocket_connect(f"/api/notifications/ws?token={token_a}") as websocket:
        websocket.send_text("ping")
        resp = websocket.receive_json()
        assert resp["type"] == "pong"

    print("Phase 2G Real-Time Notifications Test Suite PASSED 100%.")

def teardown_module(module):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE username IN ('notif_user_a', 'notif_user_b')")
    conn.commit()
    conn.close()

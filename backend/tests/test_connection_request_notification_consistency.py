import json
import pytest
from fastapi.testclient import TestClient
from app import create_app
from app.database import get_connection
from app.services.auth import hash_password, create_session

app = create_app()
client = TestClient(app)


@pytest.fixture(scope="module")
def setup_test_users():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM users WHERE email IN ('chinmayee_sync@mkc.test', 'user_b_sync@mkc.test', 'user_c_sync@mkc.test')")
    conn.commit()

    # User A (Chinmayee)
    cursor.execute(
        """
        INSERT INTO users (email, username, password_hash, full_name, mkc_id, email_verified, onboarding_completed)
        VALUES ('chinmayee_sync@mkc.test', 'chinmayee_sync', ?, 'Chinmayee Patel', 'MKC-CHIN-01', 1, 1)
        """,
        (hash_password("PasswordChin123!"),)
    )
    chinmayee_id = cursor.lastrowid

    # User B
    cursor.execute(
        """
        INSERT INTO users (email, username, password_hash, full_name, mkc_id, email_verified, onboarding_completed)
        VALUES ('user_b_sync@mkc.test', 'user_b_sync', ?, 'User B Sync', 'MKC-UB-02', 1, 1)
        """,
        (hash_password("PasswordUB123!"),)
    )
    user_b_id = cursor.lastrowid

    # User C
    cursor.execute(
        """
        INSERT INTO users (email, username, password_hash, full_name, mkc_id, email_verified, onboarding_completed)
        VALUES ('user_c_sync@mkc.test', 'user_c_sync', ?, 'User C Sync', 'MKC-UC-03', 1, 1)
        """,
        (hash_password("PasswordUC123!"),)
    )
    user_c_id = cursor.lastrowid

    conn.commit()
    conn.close()

    token_a = create_session(chinmayee_id)
    token_b = create_session(user_b_id)
    token_c = create_session(user_c_id)

    yield {
        "user_a": {"id": chinmayee_id, "token": token_a, "username": "chinmayee_sync", "name": "Chinmayee Patel"},
        "user_b": {"id": user_b_id, "token": token_b, "username": "user_b_sync", "name": "User B Sync"},
        "user_c": {"id": user_c_id, "token": token_c, "username": "user_c_sync", "name": "User C Sync"},
    }

    # Teardown
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE id IN (?, ?, ?)", (chinmayee_id, user_b_id, user_c_id))
    cursor.execute("DELETE FROM user_connections WHERE requester_id IN (?, ?, ?) OR recipient_id IN (?, ?, ?)",
                   (chinmayee_id, user_b_id, user_c_id, chinmayee_id, user_b_id, user_c_id))
    cursor.execute("DELETE FROM notifications WHERE user_id IN (?, ?, ?)", (chinmayee_id, user_b_id, user_c_id))
    conn.commit()
    conn.close()


def test_connection_request_and_notification_consistency(setup_test_users):
    user_a = setup_test_users["user_a"]
    user_b = setup_test_users["user_b"]
    user_c = setup_test_users["user_c"]

    # 1. User A (Chinmayee) sends connection request to User B
    res_req = client.post(
        "/api/social/connections/request",
        json={"user_id": user_b["id"]},
        cookies={"mkc_session": user_a["token"]}
    )
    assert res_req.status_code == 200
    req_data = res_req.json()
    assert req_data["status"] == "success"
    assert "request_id" in req_data
    request_id = req_data["request_id"]

    # 2. Invariant Check: Pending connection request exists in database
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, requester_id, recipient_id, status FROM user_connections WHERE id = ?",
        (request_id,)
    )
    conn_row = cursor.fetchone()
    assert conn_row is not None
    assert conn_row["requester_id"] == user_a["id"]
    assert conn_row["recipient_id"] == user_b["id"]
    assert conn_row["status"] == "pending"

    # 3. Invariant Check: Notification exists for User B referencing the exact connection request
    cursor.execute(
        "SELECT id, user_id, type, title, message, reference_type, reference_id, data FROM notifications WHERE user_id = ? AND type = 'connection_request'",
        (user_b["id"],)
    )
    notif_row = cursor.fetchone()
    assert notif_row is not None
    assert notif_row["reference_type"] == "connection_request"
    assert notif_row["reference_id"] == request_id
    conn.close()

    # 4. User B calls GET /api/social/connections -> MUST return pending_received with Chinmayee
    res_conns_b = client.get("/api/social/connections", cookies={"mkc_session": user_b["token"]})
    assert res_conns_b.status_code == 200
    conns_data_b = res_conns_b.json()
    pending_received = conns_data_b["pending_received"]
    assert len(pending_received) >= 1
    
    matching_req = next((r for r in pending_received if r["id"] == user_a["id"] or r.get("request_id") == request_id), None)
    assert matching_req is not None, "User B must see Chinmayee in pending_received requests"
    assert matching_req["username"] == "chinmayee_sync"
    assert matching_req["status"] == "pending"
    assert matching_req["direction"] == "received"
    assert matching_req["request_id"] == request_id

    # 5. User A calls GET /api/social/connections -> MUST see pending_sent, but NOT pending_received
    res_conns_a = client.get("/api/social/connections", cookies={"mkc_session": user_a["token"]})
    assert res_conns_a.status_code == 200
    conns_data_a = res_conns_a.json()
    assert not any(r["id"] == user_b["id"] for r in conns_data_a["pending_received"]), "User A must not see outgoing request in pending_received"
    assert any(r["id"] == user_b["id"] for r in conns_data_a["pending_sent"]), "User A must see request in pending_sent"

    # 6. User B calls GET /api/notifications -> notification contains request_id and navigation action
    res_notifs_b = client.get("/api/notifications", cookies={"mkc_session": user_b["token"]})
    assert res_notifs_b.status_code == 200
    notifs_list_b = res_notifs_b.json()
    notif_obj = next((n for n in notifs_list_b if n["type"] == "connection_request"), None)
    assert notif_obj is not None
    assert notif_obj["request_id"] == request_id
    assert notif_obj["sender_id"] == user_a["id"]
    assert notif_obj["action"] == "open_connection_requests"
    assert notif_obj["data"]["sender_username"] == "chinmayee_sync"

    # 7. User C (unauthorized) tries to view or accept User B's request -> MUST fail
    res_conns_c = client.get("/api/social/connections", cookies={"mkc_session": user_c["token"]})
    assert res_conns_c.status_code == 200
    assert not any(r.get("request_id") == request_id for r in res_conns_c.json()["pending_received"])

    # User C tries to accept by request_id
    res_c_accept_by_req = client.post(
        "/api/social/connections/accept",
        json={"request_id": request_id},
        cookies={"mkc_session": user_c["token"]}
    )
    assert res_c_accept_by_req.status_code in (400, 403, 404)

    # User C tries to accept by Chinmayee's user_id
    res_c_accept_by_user = client.post(
        "/api/social/connections/accept",
        json={"user_id": user_a["id"]},
        cookies={"mkc_session": user_c["token"]}
    )
    assert res_c_accept_by_user.status_code in (400, 403, 404)

    # 8. Duplicate Request Prevention: User A tries to send another request to User B -> 400
    res_dup = client.post(
        "/api/social/connections/request",
        json={"user_id": user_b["id"]},
        cookies={"mkc_session": user_a["token"]}
    )
    assert res_dup.status_code == 400

    # 9. User B accepts the connection using request_id
    res_accept = client.post(
        "/api/social/connections/accept",
        json={"request_id": request_id},
        cookies={"mkc_session": user_b["token"]}
    )
    assert res_accept.status_code == 200
    assert res_accept.json()["status"] == "success"

    # 10. Post-acceptance verification: Both User A and User B now see status 'accepted'
    res_conns_b_after = client.get("/api/social/connections", cookies={"mkc_session": user_b["token"]})
    assert any(c["id"] == user_a["id"] for c in res_conns_b_after.json()["accepted"])
    assert not any(c.get("request_id") == request_id for c in res_conns_b_after.json()["pending_received"])

    res_conns_a_after = client.get("/api/social/connections", cookies={"mkc_session": user_a["token"]})
    assert any(c["id"] == user_b["id"] for c in res_conns_a_after.json()["accepted"])

    # 11. User A received 'connection_accepted' notification
    res_notifs_a = client.get("/api/notifications", cookies={"mkc_session": user_a["token"]})
    assert res_notifs_a.status_code == 200
    assert any(n["type"] == "connection_accepted" for n in res_notifs_a.json())


def test_connection_rejection_flow(setup_test_users):
    user_a = setup_test_users["user_a"]
    user_c = setup_test_users["user_c"]

    # 1. User A sends connection request to User C
    res_req = client.post(
        "/api/social/connections/request",
        json={"user_id": user_c["id"]},
        cookies={"mkc_session": user_a["token"]}
    )
    assert res_req.status_code == 200
    req_id = res_req.json()["request_id"]

    # 2. User C rejects the request using request_id
    res_rej = client.post(
        "/api/social/connections/reject",
        json={"request_id": req_id},
        cookies={"mkc_session": user_c["token"]}
    )
    assert res_rej.status_code == 200

    # 3. Connection is removed
    res_conns_c = client.get("/api/social/connections", cookies={"mkc_session": user_c["token"]})
    assert not any(c.get("request_id") == req_id for c in res_conns_c.json()["pending_received"])

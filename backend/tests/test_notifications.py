import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_connection, init_db

client = TestClient(app)

def setup_module(module):
    init_db()

def test_notifications_lifecycle():
    # 1. Login user
    response = client.post("/api/auth/login", json={"identifier": "demo@masterykeycoach.com", "password": "Password123!"})
    if response.status_code != 200:
        print(response.json())
    assert response.status_code == 200
    token = response.cookies.get("mkc_session")
    headers = {"Cookie": f"mkc_session={token}"}

    # Clean existing for clean slate
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE email = 'demo@masterykeycoach.com'")
    user_id = cursor.fetchone()["id"]
    cursor.execute("DELETE FROM notifications WHERE user_id = ?", (user_id,))
    conn.commit()

    # Manually trigger a notification
    from app.services.notifications import create_notification
    import asyncio
    
    # Run async function in test
    asyncio.run(
        create_notification(
            user_id=user_id,
            type="system_alert",
            title="Test Alert",
            message="This is a test notification"
        )
    )

    # 2. Get Notifications
    response = client.get("/api/notifications", headers=headers)
    assert response.status_code == 200
    notifs = response.json()
    assert len(notifs) >= 1
    assert notifs[0]["title"] == "Test Alert"
    assert notifs[0]["is_read"] == 0
    notif_id = notifs[0]["id"]

    # 3. Mark Read
    response = client.patch(f"/api/notifications/{notif_id}/read", headers=headers)
    assert response.status_code == 200

    # 4. Verify Read
    response = client.get("/api/notifications", headers=headers)
    assert response.json()[0]["is_read"] == 1

    # 5. Create another and test Mark All Read
    asyncio.run(
        create_notification(
            user_id=user_id,
            type="system_alert",
            title="Another Alert",
            message="Test 2"
        )
    )
    
    response = client.patch("/api/notifications/read_all", headers=headers)
    assert response.status_code == 200

    response = client.get("/api/notifications", headers=headers)
    for n in response.json():
        assert n["is_read"] == 1
        
    conn.close()

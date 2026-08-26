import io
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


def setup_test_users(prefix_a: str, prefix_b: str):
    init_db()
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM user_connections WHERE requester_id IN (SELECT id FROM users WHERE email LIKE ?) OR recipient_id IN (SELECT id FROM users WHERE email LIKE ?)", (f"{prefix_a}%", f"{prefix_a}%"))
    c.execute("DELETE FROM user_connections WHERE requester_id IN (SELECT id FROM users WHERE email LIKE ?) OR recipient_id IN (SELECT id FROM users WHERE email LIKE ?)", (f"{prefix_b}%", f"{prefix_b}%"))
    c.execute("DELETE FROM chat_messages WHERE sender_id IN (SELECT id FROM users WHERE email LIKE ? OR email LIKE ?)", (f"{prefix_a}%", f"{prefix_b}%"))
    c.execute("DELETE FROM conversation_members WHERE user_id IN (SELECT id FROM users WHERE email LIKE ? OR email LIKE ?)", (f"{prefix_a}%", f"{prefix_b}%"))
    c.execute("DELETE FROM app_sessions WHERE user_id IN (SELECT id FROM users WHERE email LIKE ? OR email LIKE ?)", (f"{prefix_a}%", f"{prefix_b}%"))
    c.execute("DELETE FROM users WHERE email LIKE ? OR email LIKE ?", (f"{prefix_a}%", f"{prefix_b}%"))
    conn.commit()

    pwd = hash_password("TestPass123!")
    c.execute(
        "INSERT INTO users (email, username, password_hash, full_name, mkc_id, email_verified, onboarding_completed, avatar_initials) VALUES (?, ?, ?, ?, ?, 1, 1, ?)",
        (f"{prefix_a}@test.mkc", f"u_{prefix_a}", pwd, f"Test {prefix_a}", f"MKC-{prefix_a.upper()}", "UA"),
    )
    uid_a = c.lastrowid

    c.execute(
        "INSERT INTO users (email, username, password_hash, full_name, mkc_id, email_verified, onboarding_completed, avatar_initials) VALUES (?, ?, ?, ?, ?, 1, 1, ?)",
        (f"{prefix_b}@test.mkc", f"u_{prefix_b}", pwd, f"Test {prefix_b}", f"MKC-{prefix_b.upper()}", "UB"),
    )
    uid_b = c.lastrowid

    # Create accepted connection
    c.execute("INSERT INTO user_connections (requester_id, recipient_id, status) VALUES (?, ?, 'accepted')", (uid_a, uid_b))
    conn.commit()
    conn.close()

    token_a = create_session(uid_a)
    token_b = create_session(uid_b)
    return uid_a, token_a, uid_b, token_b


def cleanup_test_users(uid_a: int, uid_b: int):
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM user_connections WHERE requester_id IN (?, ?) OR recipient_id IN (?, ?)", (uid_a, uid_b, uid_a, uid_b))
    c.execute("DELETE FROM chat_messages WHERE sender_id IN (?, ?)", (uid_a, uid_b))
    c.execute("DELETE FROM conversation_members WHERE user_id IN (?, ?)", (uid_a, uid_b))
    c.execute("DELETE FROM app_sessions WHERE user_id IN (?, ?)", (uid_a, uid_b))
    c.execute("DELETE FROM users WHERE id IN (?, ?)", (uid_a, uid_b))
    conn.commit()
    conn.close()


def test_upload_chat_attachment_image():
    uid_a, token_a, uid_b, token_b = setup_test_users("rcht_a", "rcht_b")
    try:
        # Test image upload
        fake_image = io.BytesIO(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4")
        files = {"file": ("test_pic.png", fake_image, "image/png")}
        res = client.post("/api/chat/upload", files=files, cookies={"mkc_session": token_a})
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "success"
        assert data["file_type"] == "image"
        assert "/api/uploads/chat/" in data["url"]

        # Test audio upload
        fake_audio = io.BytesIO(b"\x1a\x45\xdf\xa3fakeaudiobytes")
        files_audio = {"file": ("voice_memo.webm", fake_audio, "audio/webm")}
        res_audio = client.post("/api/chat/upload", files=files_audio, cookies={"mkc_session": token_a})
        assert res_audio.status_code == 200
        data_audio = res_audio.json()
        assert data_audio["status"] == "success"
        assert data_audio["file_type"] == "voice"
    finally:
        cleanup_test_users(uid_a, uid_b)


def test_rich_message_history_retrieval():
    uid_a, token_a, uid_b, token_b = setup_test_users("rcht_c", "rcht_d")
    try:
        # Create conversation
        res_conv = client.post("/api/chat/conversations", json={"target_user_id": uid_b}, cookies={"mkc_session": token_a})
        assert res_conv.status_code == 200
        conv_id = res_conv.json()["id"]

        # Insert rich messages directly
        conn = get_connection()
        c = conn.cursor()
        c.execute(
            "INSERT INTO chat_messages (conversation_id, sender_id, message, message_type, attachment_url, attachment_duration) VALUES (?, ?, ?, ?, ?, ?)",
            (conv_id, uid_a, "", "image", "/api/uploads/chat/sample.png", None)
        )
        c.execute(
            "INSERT INTO chat_messages (conversation_id, sender_id, message, message_type, attachment_url, attachment_duration) VALUES (?, ?, ?, ?, ?, ?)",
            (conv_id, uid_a, "Check this voice message", "voice", "/api/uploads/chat/sample.webm", 14)
        )
        c.execute(
            "INSERT INTO chat_messages (conversation_id, sender_id, message, message_type, attachment_metadata) VALUES (?, ?, ?, ?, ?)",
            (conv_id, uid_b, "victory_trophy", "sticker", '{"sticker_id":"mkc_relentless"}')
        )
        conn.commit()
        conn.close()

        # Fetch messages
        res_msgs = client.get(f"/api/chat/conversations/{conv_id}/messages", cookies={"mkc_session": token_a})
        assert res_msgs.status_code == 200
        msgs = res_msgs.json()
        assert len(msgs) == 3
        assert msgs[0]["message_type"] == "image"
        assert msgs[0]["attachment_url"] == "/api/uploads/chat/sample.png"
        assert msgs[1]["message_type"] == "voice"
        assert msgs[1]["attachment_duration"] == 14
        assert msgs[2]["message_type"] == "sticker"
    finally:
        cleanup_test_users(uid_a, uid_b)

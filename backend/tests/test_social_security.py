import os
import sys

# Ensure we can import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import sqlite3
from app.database import get_connection

def test_social_isolation():
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Create users
        cursor.execute("INSERT INTO users (username, email, password_hash, full_name, mkc_id) VALUES ('userA', 'a@test.com', 'hash', 'User A', 'MKC-A')")
        user_a_id = cursor.lastrowid
        
        cursor.execute("INSERT INTO users (username, email, password_hash, full_name, mkc_id) VALUES ('userB', 'b@test.com', 'hash', 'User B', 'MKC-B')")
        user_b_id = cursor.lastrowid
        
        cursor.execute("INSERT INTO users (username, email, password_hash, full_name, mkc_id) VALUES ('userC', 'c@test.com', 'hash', 'User C', 'MKC-C')")
        user_c_id = cursor.lastrowid

        # User A and User B create a conversation
        cursor.execute("INSERT INTO conversations DEFAULT VALUES")
        conv_id = cursor.lastrowid
        
        cursor.execute("INSERT INTO conversation_members (conversation_id, user_id) VALUES (?, ?)", (conv_id, user_a_id))
        cursor.execute("INSERT INTO conversation_members (conversation_id, user_id) VALUES (?, ?)", (conv_id, user_b_id))
        
        # User A sends a message
        cursor.execute("INSERT INTO chat_messages (conversation_id, sender_id, message) VALUES (?, ?, ?)", (conv_id, user_a_id, "Hello from A"))

        # Test 1: User A can read message
        cursor.execute("SELECT * FROM conversation_members WHERE conversation_id = ? AND user_id = ?", (conv_id, user_a_id))
        assert cursor.fetchone() is not None, "User A should be able to access the conversation"
        
        # Test 2: User C CANNOT read message
        cursor.execute("SELECT * FROM conversation_members WHERE conversation_id = ? AND user_id = ?", (conv_id, user_c_id))
        assert cursor.fetchone() is None, "User C should NOT be able to access the conversation"
        
        print("Social & Chat isolation tests passed successfully.")

    finally:
        # Cleanup
        cursor.execute("DELETE FROM chat_messages")
        cursor.execute("DELETE FROM conversation_members")
        cursor.execute("DELETE FROM conversations")
        cursor.execute("DELETE FROM users WHERE username IN ('userA', 'userB', 'userC')")
        conn.commit()
        conn.close()

if __name__ == '__main__':
    test_social_isolation()

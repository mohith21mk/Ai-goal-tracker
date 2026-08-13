import os
import sys
import unittest

# Ensure backend path is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database import init_db, get_connection
from app.services.auth import (
    hash_password,
    verify_password,
    validate_username,
    normalize_username,
    is_username_available,
    is_email_registered,
    create_session,
    get_user_from_session,
    revoke_all_sessions,
    list_user_sessions,
    create_password_reset_token,
    verify_and_use_reset_token,
    create_email_verification_token,
    verify_email_token,
    delete_user_account,
)


class Phase11SecurityServiceTests(unittest.TestCase):

    def setUp(self):
        """Ensure database schema is initialized before running tests."""
        init_db()

    def test_password_hashing_and_verification(self):
        pwd = "SecurePassword123!"
        hashed = hash_password(pwd)
        self.assertTrue(hashed.startswith("pbkdf2_sha256$100000$"))
        self.assertTrue(verify_password(pwd, hashed))
        self.assertFalse(verify_password("WrongPassword!", hashed))

    def test_username_validation_and_normalization(self):
        # Normalization
        self.assertEqual(normalize_username("@Mohith_AI"), "mohith_ai")
        
        # Valid username
        valid, norm = validate_username("test_user_99")
        self.assertTrue(valid)
        self.assertEqual(norm, "test_user_99")

        # Invalid: too short
        valid_short, _ = validate_username("ab")
        self.assertFalse(valid_short)

        # Invalid: starts with number
        valid_num, _ = validate_username("123user")
        self.assertFalse(valid_num)

        # Invalid: reserved username
        valid_admin, _ = validate_username("admin")
        self.assertFalse(valid_admin)

    def test_registration_verification_and_reset_flow(self):
        conn = get_connection()
        cursor = conn.cursor()

        email = "test_phase11@masterykeycoach.com"
        username = "phase11_user"
        pwd = "Password123!"
        hashed_pwd = hash_password(pwd)

        # Clean prior test user if exists
        cursor.execute("DELETE FROM users WHERE LOWER(email) = ?", (email,))
        conn.commit()

        # Insert user
        cursor.execute(
            """
            INSERT INTO users (email, username, password_hash, full_name, email_verified, onboarding_completed)
            VALUES (?, ?, ?, 'Phase 11 Tester', 0, 0)
            """,
            (email, username, hashed_pwd),
        )
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()

        # Check availability
        self.assertFalse(is_username_available(username))
        self.assertTrue(is_email_registered(email))

        # 1. Create Session
        token = create_session(user_id, user_agent="Mozilla/5.0 (Windows NT 10.0)", ip_address="127.0.0.1")
        user_dict = get_user_from_session(token)
        self.assertIsNotNone(user_dict)
        self.assertEqual(user_dict["id"], user_id)
        self.assertFalse(user_dict["email_verified"])

        # List active sessions
        sessions = list_user_sessions(user_id, current_token=token)
        self.assertEqual(len(sessions), 1)
        self.assertTrue(sessions[0]["is_current"])

        # 2. Email Verification Token
        verif_token = create_email_verification_token(user_id, email)
        self.assertIsNotNone(verif_token)
        self.assertTrue(verify_email_token(verif_token))
        
        # Verify user email_verified flag updated
        user_after_verif = get_user_from_session(token)
        self.assertTrue(user_after_verif["email_verified"])

        # 3. Password Reset Flow
        reset_token = create_password_reset_token(user_id)
        self.assertIsNotNone(reset_token)
        
        new_pwd = "NewSecurePassword456!"
        self.assertTrue(verify_and_use_reset_token(reset_token, new_pwd))

        # Re-using reset token must fail
        self.assertFalse(verify_and_use_reset_token(reset_token, "AnotherPassword789!"))

        # Verify old session was revoked upon password reset
        revoked_user = get_user_from_session(token)
        self.assertIsNone(revoked_user)

        # Verify new password works
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT password_hash FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        conn.close()
        self.assertTrue(verify_password(new_pwd, row["password_hash"]))

        # 4. Account Deletion
        delete_user_account(user_id)
        self.assertTrue(is_username_available(username))
        self.assertFalse(is_email_registered(email))


if __name__ == "__main__":
    unittest.main()

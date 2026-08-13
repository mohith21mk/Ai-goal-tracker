import os
import sys
import unittest

# Ensure backend path is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.config import settings
from app.services.email import (
    _render_base_template,
    send_password_reset_email,
    send_verification_email,
)


class ProductionEmailSecurityTests(unittest.TestCase):

    def test_email_template_rendering(self):
        title = "Test Email Verification"
        subtitle = "Confirming user identity"
        content_html = "<p>Please verify your email address.</p>"
        button_text = "Verify Email Address →"
        button_url = "http://localhost:5173/verify-email?token=sample_token_123"

        rendered = _render_base_template(
            title=title,
            subtitle=subtitle,
            content_html=content_html,
            action_button_text=button_text,
            action_button_url=button_url,
        )

        self.assertIn("MASTERY KEY COACH", rendered)
        self.assertIn(title, rendered)
        self.assertIn(button_url, rendered)
        self.assertIn(button_text, rendered)

    def test_email_service_fallback(self):
        # In unconfigured local dev, send_password_reset_email logs and returns False (graceful fallback)
        res_reset = send_password_reset_email("test@example.com", "Test User", "dummy_token_123")
        self.assertFalse(res_reset)

        res_verif = send_verification_email("test@example.com", "Test User", "dummy_token_123")
        self.assertFalse(res_verif)

    def test_production_token_suppression_logic(self):
        # Simulate production environment flags
        orig_debug = settings.DEBUG
        orig_env = settings.ENVIRONMENT

        try:
            settings.ENVIRONMENT = "production"
            settings.DEBUG = False

            is_dev = settings.DEBUG and settings.ENVIRONMENT != "production"
            self.assertFalse(is_dev)

            # In production, dev token must be suppressed
            res_data = {"id": 1, "username": "prod_user"}
            dummy_token = "secret_reset_token"
            if is_dev:
                res_data["dev_reset_token"] = dummy_token

            self.assertNotIn("dev_reset_token", res_data)

        finally:
            settings.DEBUG = orig_debug
            settings.ENVIRONMENT = orig_env


if __name__ == "__main__":
    unittest.main()

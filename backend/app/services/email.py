import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

from ..config import settings

logger = logging.getLogger("mkc.email")


def _render_base_template(title: str, subtitle: str, content_html: str, action_button_text: Optional[str] = None, action_button_url: Optional[str] = None) -> str:
    """Render a premium dark-themed HTML email template matching MKC aesthetic."""
    button_html = ""
    if action_button_text and action_button_url:
        button_html = f"""
        <div style="text-align: center; margin: 32px 0;">
            <a href="{action_button_url}" target="_blank" style="display: inline-block; padding: 14px 32px; background: linear-gradient(135deg, #00E5FF 0%, #0066FF 100%); color: #030A14; font-family: 'Segoe UI', Arial, sans-serif; font-size: 15px; font-weight: 700; text-decoration: none; border-radius: 8px; box-shadow: 0 4px 20px rgba(0, 229, 255, 0.35);">
                {action_button_text}
            </a>
        </div>
        <p style="font-size: 12px; color: #64748B; text-align: center; margin-top: 16px; word-break: break-all;">
            Or copy and paste this link into your browser:<br/>
            <a href="{action_button_url}" style="color: #38BDF8; text-decoration: underline;">{action_button_url}</a>
        </p>
        """

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{title}</title>
    </head>
    <body style="margin: 0; padding: 0; background-color: #030A14; font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, sans-serif; color: #F8FAFC;">
        <table border="0" cellpadding="0" cellspacing="0" width="100%" style="table-layout: fixed;">
            <tr>
                <td align="center" style="padding: 40px 16px;">
                    <table border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width: 580px; background-color: #0A1428; border: 1px solid #1E293B; border-radius: 16px; overflow: hidden; box-shadow: 0 20px 50px rgba(0, 0, 0, 0.5);">
                        <!-- Header -->
                        <tr>
                            <td style="padding: 36px 36px 20px 36px; text-align: center; border-bottom: 1px solid #1E293B; background: linear-gradient(180deg, #0F1E38 0%, #0A1428 100%);">
                                <div style="display: inline-block; width: 44px; height: 44px; background: rgba(0, 229, 255, 0.1); border: 1px solid rgba(0, 229, 255, 0.3); border-radius: 12px; line-height: 44px; font-size: 20px;">
                                    ⚓
                                </div>
                                <h1 style="margin: 16px 0 6px 0; font-size: 22px; font-weight: 800; letter-spacing: -0.5px; color: #FFFFFF;">
                                    MASTERY KEY COACH
                                </h1>
                                <div style="font-size: 11px; font-weight: 700; letter-spacing: 2px; text-transform: uppercase; color: #38BDF8;">
                                    AI-Powered Discipline & Execution Platform
                                </div>
                            </td>
                        </tr>

                        <!-- Body -->
                        <tr>
                            <td style="padding: 36px;">
                                <h2 style="margin: 0 0 8px 0; font-size: 20px; font-weight: 700; color: #FFFFFF;">
                                    {title}
                                </h2>
                                <p style="margin: 0 0 24px 0; font-size: 14px; color: #94A3B8; line-height: 1.5;">
                                    {subtitle}
                                </p>

                                <div style="font-size: 14px; color: #CBD5E1; line-height: 1.6;">
                                    {content_html}
                                </div>

                                {button_html}
                            </td>
                        </tr>

                        <!-- Footer -->
                        <tr>
                            <td style="padding: 24px 36px; background-color: #050B16; border-top: 1px solid #1E293B; text-align: center;">
                                <p style="margin: 0; font-size: 12px; color: #64748B; line-height: 1.5;">
                                    This automated security notification was dispatched by <strong>Mastery Key Coach</strong>.<br/>
                                    If you did not initiate this request, please secure your account immediately.
                                </p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """


def send_email_via_smtp(to_email: str, subject: str, html_content: str, text_content: str) -> bool:
    """Send email over SMTP if configured; otherwise log to stdout in development."""
    if not settings.SMTP_HOST:
        logger.info(f"[DEV EMAIL SYSTEM] SMTP_HOST unconfigured. Email payload to <{to_email}> Subject: '{subject}'")
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
        msg["To"] = to_email

        msg.attach(MIMEText(text_content, "plain", "utf-8"))
        msg.attach(MIMEText(html_content, "html", "utf-8"))

        if settings.SMTP_USE_TLS:
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                if settings.SMTP_USER and settings.SMTP_PASSWORD:
                    server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.sendmail(settings.SMTP_FROM_EMAIL, [to_email], msg.as_string())
        else:
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                if settings.SMTP_USER and settings.SMTP_PASSWORD:
                    server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.sendmail(settings.SMTP_FROM_EMAIL, [to_email], msg.as_string())

        logger.info(f"Successfully sent email via SMTP to <{to_email}>")
        return True
    except Exception as err:
        logger.error(f"Failed to send email via SMTP to <{to_email}>: {err}")
        return False


def send_password_reset_email(to_email: str, recipient_name: str, token: str) -> bool:
    """Send password reset recovery email to recipient."""
    reset_url = f"{settings.APP_FRONTEND_URL}/reset-password?token={token}"
    subject = "Mastery Key Coach — Password Reset Instructions"
    title = "Reset Your Password"
    subtitle = f"Hello {recipient_name or 'Member'}, a password reset request was initiated for your MKC account."

    content_html = """
    <p>We received a request to reset the password for your account. Click the button below to choose a new password. This single-use link will expire in <strong>15 minutes</strong>.</p>
    """
    text_content = f"Hello {recipient_name},\n\nReset your password for Mastery Key Coach by visiting:\n{reset_url}\n\nThis link will expire in 15 minutes."

    html_content = _render_base_template(
        title=title,
        subtitle=subtitle,
        content_html=content_html,
        action_button_text="Reset Password →",
        action_button_url=reset_url,
    )
    return send_email_via_smtp(to_email, subject, html_content, text_content)


def send_verification_email(to_email: str, recipient_name: str, token: str) -> bool:
    """Send email address verification email to recipient."""
    verif_url = f"{settings.APP_FRONTEND_URL}/verify-email?token={token}"
    subject = "Mastery Key Coach — Verify Your Email Address"
    title = "Verify Your Account Email"
    subtitle = f"Welcome to Mastery Key Coach, {recipient_name or 'Member'}!"

    content_html = """
    <p>Please confirm your email address to ensure account recovery access and receive system notifications. Click the button below to verify your email address.</p>
    """
    text_content = f"Welcome {recipient_name},\n\nPlease verify your email address for Mastery Key Coach by visiting:\n{verif_url}\n"

    html_content = _render_base_template(
        title=title,
        subtitle=subtitle,
        content_html=content_html,
        action_button_text="Verify Email Address →",
        action_button_url=verif_url,
    )
    return send_email_via_smtp(to_email, subject, html_content, text_content)

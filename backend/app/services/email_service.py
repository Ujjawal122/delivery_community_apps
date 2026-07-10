from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from pydantic import NameEmail, SecretStr
from app.config import settings


# ── SMTP connection config (built once at import time) ─────────────
_mail_config = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=SecretStr(settings.MAIL_PASSWORD),
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_STARTTLS=settings.MAIL_STARTTLS,
    MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
)

_mailer = FastMail(_mail_config)


class EmailService:
    """Sends transactional emails (verification, password-reset)."""

    # ── Email Verification ─────────────────────────────────────────

    @staticmethod
    async def send_verification_email(email: str, token: str) -> None:
        """Send an account-verification link to the user's email address."""
        verify_url = f"{settings.FRONTEND_URL}/auth/verify-email?token={token}"

        html_body = f"""
        <html>
          <body style="font-family: Arial, sans-serif; background:#f4f4f4; padding:30px;">
            <div style="max-width:500px;margin:auto;background:#fff;border-radius:8px;
                        padding:32px;box-shadow:0 2px 8px rgba(0,0,0,.12);">
              <h2 style="color:#1a1a2e;">Verify your email address</h2>
              <p style="color:#444;line-height:1.6;">
                Welcome to <strong>Delivery Community</strong>!<br>
                Click the button below to verify your email address.
                This link expires in <strong>24 hours</strong>.
              </p>
              <a href="{verify_url}"
                 style="display:inline-block;margin-top:20px;padding:12px 28px;
                        background:#4f46e5;color:#fff;border-radius:6px;
                        text-decoration:none;font-weight:600;">
                Verify Email
              </a>
              <p style="margin-top:24px;color:#888;font-size:13px;">
                If you didn't create an account, you can safely ignore this email.
              </p>
            </div>
          </body>
        </html>
        """

        message = MessageSchema(
            subject="Verify your Delivery Community account",
          recipients=[NameEmail(name=email, email=email)],
            body=html_body,
            subtype=MessageType.html,
        )
        await _mailer.send_message(message)

    # ── Password Reset ─────────────────────────────────────────────

    @staticmethod
    async def send_password_reset_email(email: str, token: str) -> None:
        """Send a password-reset link to the user's email address."""
        reset_url = f"{settings.FRONTEND_URL}/auth/reset-password?token={token}"

        html_body = f"""
        <html>
          <body style="font-family: Arial, sans-serif; background:#f4f4f4; padding:30px;">
            <div style="max-width:500px;margin:auto;background:#fff;border-radius:8px;
                        padding:32px;box-shadow:0 2px 8px rgba(0,0,0,.12);">
              <h2 style="color:#1a1a2e;">Reset your password</h2>
              <p style="color:#444;line-height:1.6;">
                We received a request to reset the password for your
                <strong>Delivery Community</strong> account.<br>
                Click the button below to choose a new password.
                This link expires in <strong>1 hour</strong>.
              </p>
              <a href="{reset_url}"
                 style="display:inline-block;margin-top:20px;padding:12px 28px;
                        background:#e53e3e;color:#fff;border-radius:6px;
                        text-decoration:none;font-weight:600;">
                Reset Password
              </a>
              <p style="margin-top:24px;color:#888;font-size:13px;">
                If you did not request a password reset, you can safely ignore this email.
              </p>
            </div>
          </body>
        </html>
        """

        message = MessageSchema(
            subject="Reset your Delivery Community password",
          recipients=[NameEmail(name=email, email=email)],
            body=html_body,
            subtype=MessageType.html,
        )
        await _mailer.send_message(message)

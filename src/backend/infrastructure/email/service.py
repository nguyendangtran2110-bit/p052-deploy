from __future__ import annotations

import logging
import smtplib
from email.message import EmailMessage
from urllib.parse import quote

from src.backend.core.config import Settings

logger = logging.getLogger(__name__)


class EmailService:
    def __init__(self, settings: Settings):
        self.settings = settings

    def send_password_reset_email(self, recipient: str, raw_token: str) -> None:
        reset_url = f"{self.settings.password_reset_url_base}?token={quote(raw_token)}"
        message = EmailMessage()
        message["Subject"] = "Reset your OnBxrd password"
        message["From"] = self.settings.smtp_from_email
        message["To"] = recipient
        message.set_content(
            "A password reset was requested for your account.\n\n"
            f"Open this link within {self.settings.password_reset_token_minutes} minutes:\n{reset_url}\n\n"
            "If you did not request this, you can ignore this email."
        )
        self._send(message, "password reset")

    def send_email_verification_code(self, recipient: str, raw_code: str) -> None:
        message = EmailMessage()
        message["Subject"] = "Verify your OnBxrd email"
        message["From"] = self.settings.smtp_from_email
        message["To"] = recipient
        message.set_content(
            "Your OnBxrd email verification code is:\n\n"
            f"{raw_code}\n\n"
            f"This code expires in {self.settings.email_verification_token_minutes} minutes.\n"
            "If you did not request an account, you can ignore this email."
        )
        self._send(message, "email verification")

    def _send(self, message: EmailMessage, purpose: str) -> None:
        if not self.settings.smtp_host or not self.settings.smtp_from_email:
            logger.warning("SMTP is not configured; %s email was not sent", purpose)
            return

        with smtplib.SMTP(self.settings.smtp_host, self.settings.smtp_port, timeout=15) as smtp:
            if self.settings.smtp_use_tls:
                smtp.starttls()
            if self.settings.smtp_username:
                smtp.login(self.settings.smtp_username, self.settings.smtp_password)
            smtp.send_message(message)

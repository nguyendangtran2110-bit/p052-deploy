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
        if not self.settings.smtp_host or not self.settings.smtp_from_email:
            logger.warning("SMTP is not configured; password reset email was not sent")
            return

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

        with smtplib.SMTP(self.settings.smtp_host, self.settings.smtp_port, timeout=15) as smtp:
            if self.settings.smtp_use_tls:
                smtp.starttls()
            if self.settings.smtp_username:
                smtp.login(self.settings.smtp_username, self.settings.smtp_password)
            smtp.send_message(message)

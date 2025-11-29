import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.mime.audio import MIMEAudio
import os
from typing import Union, List, Optional
from config.settings import settings
import logging

logger = logging.getLogger(__name__)


class EmailClient:
    def __init__(self):
        self.smtp_server = settings.SMTP_SERVER
        self.smtp_port = settings.SMTP_PORT
        self.smtp_user = settings.SMTP_USER
        self.smtp_password = settings.SMTP_PASSWORD
        self.email_from = settings.EMAIL_FROM
        self.email_to = settings.EMAIL_TO

    def send_email(
        self,
        subject: str,
        body: str,
        attachment_path: Optional[Union[str, List[str]]] = None
    ):
        """Sends an email with optional attachment(s)."""
        msg = MIMEMultipart()
        msg['From'] = self.email_from
        msg['To'] = self.email_to
        msg['Subject'] = subject

        msg.attach(MIMEText(body, 'html'))

        # Handle single or multiple attachments
        attachments = []
        if attachment_path:
            if isinstance(attachment_path, str):
                attachments = [attachment_path]
            else:
                attachments = attachment_path

        for path in attachments:
            if path and os.path.exists(path):
                self._attach_file(msg, path)

        try:
            if self.smtp_server == "localhost":
                # For dev/testing, just log it
                logger.info(
                    f"Mock sending email to {self.email_to} with subject '{subject}'")
                return

            if self.smtp_port == 465:
                # Use SMTP_SSL for port 465
                with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port) as server:
                    if self.smtp_user and self.smtp_password:
                        server.login(self.smtp_user, self.smtp_password)
                    server.send_message(msg)
            else:
                # Use SMTP + STARTTLS for other ports (e.g., 587)
                with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                    if self.smtp_user and self.smtp_password:
                        server.starttls()
                        server.login(self.smtp_user, self.smtp_password)
                    server.send_message(msg)

            logger.info(f"Email sent successfully to {self.email_to}")
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            raise

    def _attach_file(self, msg: MIMEMultipart, file_path: str):
        """Attach a file to the email message."""
        filename = os.path.basename(file_path)

        # Determine MIME type based on extension
        if file_path.endswith('.mp3'):
            with open(file_path, "rb") as f:
                part = MIMEAudio(f.read(), _subtype='mpeg')
        else:
            with open(file_path, "rb") as f:
                part = MIMEApplication(f.read(), Name=filename)

        part['Content-Disposition'] = f'attachment; filename="{filename}"'
        msg.attach(part)
        logger.info(f"Attached file: {filename}")

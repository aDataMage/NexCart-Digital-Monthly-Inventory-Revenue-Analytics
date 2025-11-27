import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import os
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

    def send_email(self, subject: str, body: str, attachment_path: str = None):
        """Sends an email with an optional attachment."""
        msg = MIMEMultipart()
        msg['From'] = self.email_from
        msg['To'] = self.email_to
        msg['Subject'] = subject

        msg.attach(MIMEText(body, 'html'))

        if attachment_path and os.path.exists(attachment_path):
            with open(attachment_path, "rb") as f:
                part = MIMEApplication(f.read(), Name=os.path.basename(attachment_path))
            part['Content-Disposition'] = f'attachment; filename="{os.path.basename(attachment_path)}"'
            msg.attach(part)

        try:
            if self.smtp_server == "localhost":
                # For dev/testing, just log it
                logger.info(f"Mock sending email to {self.email_to} with subject '{subject}'")
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

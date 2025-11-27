import sys
import os
import logging

# Add project root to path
sys.path.append(os.getcwd())

from src.email_client import EmailClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_email():
    logger.info("Testing Email Credentials...")
    client = EmailClient()
    try:
        client.send_email(
            subject="Test Email from Pipeline",
            body="<h1>It works!</h1><p>This is a test email to verify credentials.</p>"
        )
        logger.info("Email test PASSED.")
    except Exception as e:
        logger.error(f"Email test FAILED: {e}")

if __name__ == "__main__":
    test_email()

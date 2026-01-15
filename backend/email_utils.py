"""
Email utility for sending signup notifications
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
import os

logger = logging.getLogger(__name__)

# Email configuration
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "hajar.assim@gmail.com")
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")


def send_signup_notification(user_email: str, user_name: str = None) -> bool:
    """
    Send email notification to admin when a user requests access

    Args:
        user_email: The email of the user requesting access
        user_name: Optional name of the user

    Returns:
        True if email sent successfully, False otherwise
    """
    if not SMTP_USERNAME or not SMTP_PASSWORD:
        logger.warning("SMTP credentials not configured. Skipping email notification.")
        logger.info(f"User signup request: {user_email} ({user_name or 'No name'})")
        return False

    try:
        # Create message
        msg = MIMEMultipart('alternative')
        msg['From'] = SMTP_USERNAME
        msg['To'] = ADMIN_EMAIL
        msg['Subject'] = f"musik-ai: New User Access Request - {user_email}"

        # Create email body
        dashboard_link = "https://developer.spotify.com/dashboard/b3ecd97e613e4dc58cfbecb9c8cb6c54/users"

        text_body = f"""
New User Access Request for musik-ai

User Email: {user_email}
User Name: {user_name or 'Not provided'}

To add this user to your Spotify app:
1. Visit: {dashboard_link}
2. Add the user's email: {user_email}
3. Click 'Add User'

This is an automated message from musik-ai.
"""

        html_body = f"""
<html>
<head></head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #334389;">musik-ai: New User Access Request</h2>

        <div style="background-color: #f4f4f1; padding: 20px; border-radius: 8px; margin: 20px 0;">
            <p><strong>User Email:</strong> {user_email}</p>
            <p><strong>User Name:</strong> {user_name or 'Not provided'}</p>
        </div>

        <h3 style="color: #334389;">Action Required:</h3>
        <ol>
            <li>Visit the <a href="{dashboard_link}" style="color: #334389;">Spotify Dashboard Users Page</a></li>
            <li>Add the user's email: <code style="background: #e6c5a3; padding: 2px 6px; border-radius: 3px;">{user_email}</code></li>
            <li>Click 'Add User'</li>
        </ol>

        <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #c6d1e0; color: #6d5666; font-size: 12px;">
            <p>This is an automated message from musik-ai.</p>
        </div>
    </div>
</body>
</html>
"""

        # Attach both plain and HTML parts
        part1 = MIMEText(text_body, 'plain')
        part2 = MIMEText(html_body, 'html')
        msg.attach(part1)
        msg.attach(part2)

        # Send email
        logger.info(f"Sending signup notification to {ADMIN_EMAIL} for user {user_email}")

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)

        logger.info("✓ Signup notification sent successfully")
        return True

    except Exception as e:
        logger.error(f"Failed to send signup notification: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        return False

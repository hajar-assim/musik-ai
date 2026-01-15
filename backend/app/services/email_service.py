import resend
import logging
from app.config import settings

logger = logging.getLogger(__name__)

DASHBOARD_LINK = "https://developer.spotify.com/dashboard/b3ecd97e613e4dc58cfbecb9c8cb6c54/users"


def send_signup_notification(user_email: str, user_name: str = None) -> bool:
    """Send email notification to admin for new user access request using Resend"""
    if not settings.RESEND_API_KEY or not settings.RESEND_API_KEY.strip():
        logger.info(f"Resend API not configured. Logging access request: {user_email} ({user_name or 'No name'})")
        return False

    try:
        resend.api_key = settings.RESEND_API_KEY

        html_body = f"""
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #334389;">musik-ai: New User Access Request</h2>
        <div style="background-color: #f4f4f1; padding: 20px; border-radius: 8px; margin: 20px 0;">
            <p><strong>User Email:</strong> {user_email}</p>
            <p><strong>User Name:</strong> {user_name or 'Not provided'}</p>
        </div>
        <h3 style="color: #334389;">Action Required:</h3>
        <ol>
            <li>Visit the <a href="{DASHBOARD_LINK}" style="color: #334389;">Spotify Dashboard</a></li>
            <li>Add: <code style="background: #e6c5a3; padding: 2px 6px; border-radius: 3px;">{user_email}</code></li>
            <li>Click 'Add User'</li>
        </ol>
        <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #c6d1e0; color: #6d5666; font-size: 12px;">
            <p>Automated message from musik-ai</p>
        </div>
    </div>
</body>
</html>
"""

        logger.info(f"Sending notification to {settings.ADMIN_EMAIL} for {user_email}")

        params = {
            "from": f"musik-ai <{settings.RESEND_FROM_EMAIL}>",
            "to": [settings.ADMIN_EMAIL],
            "subject": f"musik-ai: New User Access Request - {user_email}",
            "html": html_body,
        }

        email = resend.Emails.send(params)
        logger.info(f"✓ Notification sent via Resend (ID: {email.get('id')})")
        return True

    except Exception as e:
        logger.error(f"Failed to send notification via Resend: {e}")
        logger.info(f"Access request (fallback log): {user_email} ({user_name or 'No name'})")
        return False

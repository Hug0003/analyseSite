"""
Notification Service
Handles email notifications using FastAPI-Mail
"""
from typing import List
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from pydantic import EmailStr
from ..config import get_settings

settings = get_settings()

conf = ConnectionConfig(
    MAIL_USERNAME=settings.mail_username,
    MAIL_PASSWORD=settings.mail_password,
    MAIL_FROM=settings.mail_from,
    MAIL_PORT=settings.mail_port,
    MAIL_SERVER=settings.mail_server,
    MAIL_STARTTLS=settings.mail_starttls,
    MAIL_SSL_TLS=settings.mail_ssl_tls,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=False, # Dev only
)

async def send_email(subject: str, recipients: List[EmailStr], body: str):
    """Generic email sender"""
    if not settings.mail_password or not settings.mail_server:
        print(f"[Simulated Email] To: {recipients}, Subject: {subject}, Body: {body[:50]}...")
        return

    message = MessageSchema(
        subject=subject,
        recipients=recipients,
        body=body,
        subtype=MessageType.html
    )

    fm = FastMail(conf)
    await fm.send_message(message)

async def send_alert_email(to_email: str, url: str, old_score: int, new_score: int):
    """Send Alert when score drops"""
    subject = f"🚨 Alert: Check Security Score dropped for {url}"
    
    html = f"""
    <div style="font-family: Arial, sans-serif; padding: 20px; border: 1px solid #ddd; max-width: 600px;">
        <h2 style="color: #e74c3c;">Score Warning</h2>
        <p>Your monitored website has detected a performance/security drop.</p>
        
        <div style="background: #f9f9f9; padding: 15px; border-radius: 5px; margin: 20px 0;">
            <p><strong>URL:</strong> <a href="{url}">{url}</a></p>
            <p><strong>Previous Score:</strong> <span style="font-size: 1.2em; color: #7f8c8d;">{old_score}</span></p>
            <p><strong>Current Score:</strong> <span style="font-size: 1.5em; font-weight: bold; color: #c0392b;">{new_score}</span></p>
        </div>
        
        <p>Please check your dashboard for detailed analysis.</p>
        <br>
        <p style="font-size: 0.8em; color: gray;">This is an automated message from SiteAuditor Watchdog.</p>
    </div>
    """
    
    await send_email(subject, [to_email], html)

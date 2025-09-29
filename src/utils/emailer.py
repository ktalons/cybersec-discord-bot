from email.message import EmailMessage
import smtplib
from typing import Optional


def send_email_smtp_ssl(host: str, port: int, user: str, app_password: str, to_email: str, subject: str, body: str) -> bool:
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = user
    msg["To"] = to_email
    msg.set_content(body)

    try:
        with smtplib.SMTP_SSL(host, port) as smtp:
            smtp.login(user, app_password)
            smtp.send_message(msg)
        return True
    except Exception as e:
        print(f"Email send error: {e}")
        return False

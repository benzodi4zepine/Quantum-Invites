import smtplib
from email.message import EmailMessage
from typing import Optional

from app.bot.helper import confighelper


def is_email_configured() -> bool:
    return (
        confighelper.SUBSCRIPTION_EMAIL_ENABLED
        and confighelper.SMTP_HOST
        and confighelper.SMTP_FROM_EMAIL
    )


def send_email(subject: str, body: str, to_email: str) -> bool:
    if not is_email_configured():
        return False

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = confighelper.SMTP_FROM_EMAIL
    message["To"] = to_email
    message.set_content(body)

    try:
        if confighelper.SMTP_USE_TLS:
            with smtplib.SMTP(confighelper.SMTP_HOST, confighelper.SMTP_PORT, timeout=15) as server:
                server.ehlo()
                server.starttls()
                if confighelper.SMTP_USERNAME and confighelper.SMTP_PASSWORD:
                    server.login(confighelper.SMTP_USERNAME, confighelper.SMTP_PASSWORD)
                server.send_message(message)
        else:
            with smtplib.SMTP(confighelper.SMTP_HOST, confighelper.SMTP_PORT, timeout=15) as server:
                if confighelper.SMTP_USERNAME and confighelper.SMTP_PASSWORD:
                    server.login(confighelper.SMTP_USERNAME, confighelper.SMTP_PASSWORD)
                server.send_message(message)
        return True
    except Exception as exc:
        print(f"Failed to send email to {to_email}: {exc}")
        return False

import os
import smtplib
from email.message import EmailMessage

from dotenv import load_dotenv

load_dotenv()


def send_password_reset_email(recipient: str, reset_link: str) -> None:
    """Send a password-reset link through Gmail SMTP."""

    sender = os.getenv("SMTP_EMAIL")
    app_password = os.getenv("SMTP_APP_PASSWORD")

    if not sender or not app_password:
        raise RuntimeError("Gmail SMTP settings are missing.")

    message = EmailMessage()
    message["Subject"] = "VehicleWise - Password Reset"
    message["From"] = sender
    message["To"] = recipient

    message.set_content(
        f"""
Hello,

We received a request to reset your VehicleWise password.

Use the link below to choose a new password:

{reset_link}

This link expires in 15 minutes and can only be used once.

If you did not request this reset, you can ignore this email.

VehicleWise Team
"""
    )

    with smtplib.SMTP("smtp.gmail.com", 587, timeout=20) as server:
        server.starttls()
        server.login(sender, app_password)
        server.send_message(message)

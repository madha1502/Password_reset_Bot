import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from sqlalchemy.orm import Session
from models import MockEmail
from datetime import datetime

def send_otp_email(db: Session, to_email: str, otp: str) -> bool:
    subject = "Your Password Reset OTP Verification Code"
    body = f"""Hello,

We received a request to reset your password. Use the verification code below to proceed:

=== OTP CODE ===
{otp}
===============

This code is valid for 10 minutes. If you did not request a password reset, please ignore this email.

Best regards,
IT Helpdesk Bot
"""
    # 1. Store email in SQLite for frontend mock inbox
    try:
        mock_email = MockEmail(
            to_email=to_email,
            subject=subject,
            body=body,
            sent_at=datetime.utcnow()
        )
        db.add(mock_email)
        db.commit()
        db.refresh(mock_email)
        print(f"[Email Service] Mock email saved to DB. ID: {mock_email.id}, OTP: {otp}")
    except Exception as db_err:
        print(f"[Email Service] Error saving email to DB: {db_err}")

    # 2. Try sending via SMTP if environment variables are set
    host = os.getenv("MAIL_HOST")
    port_str = os.getenv("MAIL_PORT")
    username = os.getenv("MAIL_USERNAME")
    password = os.getenv("MAIL_PASSWORD")
    sender = os.getenv("MAIL_FROM", "support@company.com")

    if host and port_str and username and password:
        try:
            port = int(port_str)
            msg = MIMEMultipart()
            msg["From"] = sender
            msg["To"] = to_email
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "plain"))

            # Establish SMTP connection
            server = smtplib.SMTP(host, port)
            server.starttls()
            server.login(username, password)
            server.sendmail(sender, to_email, msg.as_string())
            server.quit()
            print(f"[Email Service] Email sent successfully via SMTP to {to_email}")
            return True
        except Exception as smtp_err:
            print(f"[Email Service] Failed to send email via SMTP: {smtp_err}")
            return False
    else:
        print("[Email Service] SMTP parameters missing or incomplete. Skipping SMTP delivery (using mock inbox).")
        return True

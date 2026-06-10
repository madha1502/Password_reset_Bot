import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from sqlalchemy.orm import Session
from models import MockEmail, User
from datetime import datetime
from fastapi import HTTPException, status

def send_otp_email(db: Session, to_email: str, otp: str) -> bool:
    # 1. Check for missing configuration
    host = os.getenv("MAIL_SERVER")
    port_str = os.getenv("MAIL_PORT")
    username = os.getenv("MAIL_USERNAME")
    password = os.getenv("MAIL_PASSWORD")
    use_tls_str = os.getenv("MAIL_USE_TLS", "True")

    if not host or not port_str or not username or not password:
        missing_vars = []
        if not host: missing_vars.append("MAIL_SERVER")
        if not port_str: missing_vars.append("MAIL_PORT")
        if not username: missing_vars.append("MAIL_USERNAME")
        if not password: missing_vars.append("MAIL_PASSWORD")
        error_msg = f"Missing mail configuration variables: {', '.join(missing_vars)}."
        print(f"[Email Service] {error_msg}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"SMTP mail server is not configured. Please define: {', '.join(missing_vars)} in the .env file."
        )

    if username == "<gmail_address>" or password == "<gmail_app_password>":
        print("[Email Service] SMTP configuration is using placeholder values. Please update the .env file.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="SMTP mail server is configured with placeholders. Please replace <gmail_address> and <gmail_app_password> in the .env file."
        )

    # 2. Fetch user greeting name
    user = db.query(User).filter(User.email == to_email).first()
    name = user.name if user and user.name else "User"

    # 3. Create Subject and Body
    subject = "Password Reset OTP"
    
    # HTML template
    html_body = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Password Reset OTP</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: #f4f4f5;
            color: #18181b;
            padding: 32px 16px;
            margin: 0;
        }}
        .container {{
            max-width: 512px;
            margin: 0 auto;
            background-color: #ffffff;
            border: 1px solid #e4e4e7;
            border-radius: 8px;
            padding: 32px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        }}
        .header {{
            margin-bottom: 24px;
            text-align: center;
        }}
        .logo {{
            font-size: 20px;
            font-weight: 700;
            color: #09090b;
            letter-spacing: -0.05em;
        }}
        .branding-divider {{
            height: 1px;
            background-color: #e4e4e7;
            margin: 16px 0 24px;
        }}
        .greeting {{
            font-size: 16px;
            line-height: 24px;
            margin-bottom: 16px;
        }}
        .intro {{
            font-size: 14px;
            line-height: 20px;
            color: #52525b;
            margin-bottom: 24px;
        }}
        .otp-container {{
            background-color: #f4f4f5;
            border: 1px solid #e4e4e7;
            border-radius: 6px;
            padding: 16px;
            text-align: center;
            margin-bottom: 24px;
        }}
        .otp-code {{
            font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
            font-size: 32px;
            font-weight: 700;
            letter-spacing: 0.1em;
            color: #09090b;
        }}
        .expiry-info {{
            font-size: 13px;
            color: #71717a;
            margin-top: 8px;
        }}
        .security-warning {{
            font-size: 12px;
            line-height: 18px;
            color: #e11d48;
            background-color: #fff1f2;
            border: 1px solid #ffe4e6;
            border-radius: 6px;
            padding: 12px 16px;
            margin-bottom: 24px;
        }}
        .footer {{
            text-align: center;
            font-size: 12px;
            color: #a1a1aa;
            margin-top: 32px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">🔐 Identity Portal</div>
            <div class="branding-divider"></div>
        </div>
        <div class="greeting">Hello {name},</div>
        <div class="intro">
            We received a request to reset your password for your Identity Portal account. Please use the following One-Time Password (OTP) to complete the verification process.
        </div>
        <div class="otp-container">
            <div class="otp-code">{otp}</div>
            <div class="expiry-info">This code is valid for <strong>5 minutes</strong>.</div>
        </div>
        <div class="security-warning">
            <strong>Security Warning:</strong> For your security, never share this OTP with anyone, including support staff. Our team will never ask you for your verification code.
        </div>
        <div class="intro">
            If you did not request this password reset, please ignore this email or contact support if you have concerns.
        </div>
        <div class="footer">
            &copy; 2026 Identity Portal. All rights reserved.
        </div>
    </div>
</body>
</html>
"""

    plain_body = f"""Hello {name},

We received a request to reset your password for your Identity Portal account. Please use the following One-Time Password (OTP) to complete the verification process.

=== OTP CODE ===
{otp}
===============

This code is valid for 5 minutes.

Security Warning: For your security, never share this OTP with anyone, including support staff. Our team will never ask you for your verification code.

If you did not request this password reset, please ignore this email.

Best regards,
Identity Portal Team
"""

    # 4. Save mock email to DB with OTP redacted/masked
    try:
        masked_plain_body = plain_body.replace(otp, "******")
        mock_email = MockEmail(
            to_email=to_email,
            subject=subject,
            body=masked_plain_body,
            sent_at=datetime.utcnow()
        )
        db.add(mock_email)
        db.commit()
        db.refresh(mock_email)
        print(f"[Email Service] Mock email saved to DB. ID: {mock_email.id} (OTP redacted)")
    except Exception as db_err:
        print(f"[Email Service] Error saving mock email: {db_err}")

    # 5. Connect and send email via SMTP
    try:
        port = int(port_str)
        msg = MIMEMultipart("alternative")
        msg["From"] = username
        msg["To"] = to_email
        msg["Subject"] = subject

        # Attach text and html parts
        part1 = MIMEText(plain_body, "plain")
        part2 = MIMEText(html_body, "html")
        msg.attach(part1)
        msg.attach(part2)

        # Establish connection
        server = smtplib.SMTP(host, port, timeout=10.0)
        
        # Check TLS
        if use_tls_str.lower() in ("true", "1", "yes"):
            server.starttls()
            
        server.login(username, password)
        server.sendmail(username, to_email, msg.as_string())
        server.quit()
        print(f"[Email Service] Email sent successfully via SMTP to {to_email}")
        return True
    except Exception as smtp_err:
        print(f"[Email Service] Failed to send email via SMTP: {smtp_err}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send email via SMTP server due to a connection or authentication failure: {str(smtp_err)}"
        )

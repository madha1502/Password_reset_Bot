import os
import resend
from sqlalchemy.orm import Session
from models import MockEmail, User
from datetime import datetime
from fastapi import HTTPException, status

def send_otp_email(db: Session, to_email: str, otp: str) -> bool:
    # 1. Check for required Resend API key
    api_key = os.getenv("RESEND_API_KEY")
    mail_from = os.getenv("MAIL_FROM", "Identity Portal <onboarding@resend.dev>")

    if not api_key:
        print("[Email Service] RESEND_API_KEY is not set in environment variables.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Email service is not configured. Please set RESEND_API_KEY in your environment variables."
        )

    # 2. Fetch user greeting name
    user = db.query(User).filter(User.email == to_email).first()
    name = user.name if user and user.name else "User"

    # 3. Build professional HTML email body
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
        .logo {{
            font-size: 20px;
            font-weight: 700;
            color: #09090b;
            letter-spacing: -0.05em;
            text-align: center;
            margin-bottom: 16px;
        }}
        .divider {{
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
            padding: 20px;
            text-align: center;
            margin-bottom: 24px;
        }}
        .otp-label {{
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            color: #71717a;
            margin-bottom: 8px;
        }}
        .otp-code {{
            font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
            font-size: 36px;
            font-weight: 700;
            letter-spacing: 0.15em;
            color: #09090b;
        }}
        .expiry-info {{
            font-size: 13px;
            color: #71717a;
            margin-top: 8px;
        }}
        .warning {{
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
        <div class="logo">🔐 Identity Portal</div>
        <div class="divider"></div>
        <div class="greeting">Hello {name},</div>
        <div class="intro">
            We received a request to reset the password for your Identity Portal account.
            Use the OTP below to complete your verification.
        </div>
        <div class="otp-container">
            <div class="otp-label">Your One-Time Password</div>
            <div class="otp-code">{otp}</div>
            <div class="expiry-info">Valid for <strong>5 minutes</strong> only.</div>
        </div>
        <div class="warning">
            <strong>⚠️ Security Warning:</strong> Never share this OTP with anyone — including support staff.
            Our team will never ask for your verification code.
        </div>
        <div class="intro">
            If you did not request this password reset, please ignore this email.
            Your account remains secure.
        </div>
        <div class="footer">
            &copy; 2026 Identity Portal. All rights reserved.
        </div>
    </div>
</body>
</html>"""

    plain_body = f"""Hello {name},

We received a request to reset the password for your Identity Portal account.

=== YOUR OTP CODE ===
{otp}
====================

This code is valid for 5 minutes only.

SECURITY WARNING: Never share this OTP with anyone, including support staff.
Our team will never ask for your verification code.

If you did not request this reset, please ignore this email.

Best regards,
Identity Portal Team
"""

    # 4. Save masked mock email to DB (OTP redacted)
    try:
        masked_body = plain_body.replace(otp, "******")
        mock_email = MockEmail(
            to_email=to_email,
            subject="Password Reset OTP",
            body=masked_body,
            sent_at=datetime.utcnow()
        )
        db.add(mock_email)
        db.commit()
        db.refresh(mock_email)
        print(f"[Email Service] Mock email saved to DB. ID: {mock_email.id} (OTP redacted)")
    except Exception as db_err:
        print(f"[Email Service] Error saving mock email: {db_err}")

    # 5. Send via Resend HTTP API
    try:
        resend.api_key = api_key
        params: resend.Emails.SendParams = {
            "from": mail_from,
            "to": [to_email],
            "subject": "Password Reset OTP",
            "html": html_body,
            "text": plain_body
        }
        email_response = resend.Emails.send(params)
        print(f"[Email Service] Email sent via Resend. ID: {email_response.get('id', 'N/A')}")
        return True
    except Exception as e:
        print(f"[Email Service] Resend API error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send email: {str(e)}"
        )

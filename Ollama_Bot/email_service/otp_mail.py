import os
import json
import urllib.request
import urllib.error


def send_otp_email(to_email: str, otp: str, name: str = "User") -> bool:
    """Send OTP email via SendGrid HTTP API."""
    api_key   = os.getenv("SENDGRID_API_KEY")
    mail_from = os.getenv("MAIL_FROM", "noreply@example.com")

    if not api_key or "your-sendgrid-api-key" in api_key or api_key.startswith("<"):
        print("\n" + "="*60)
        print(f"  [DEV MODE] OTP Email for {to_email} ({name})")
        print(f"  Your 6-Digit OTP Code is: {otp}")
        print("="*60 + "\n")
        return True

    html_body = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><style>
body{{font-family:Arial,sans-serif;background:#f4f4f5;padding:32px 16px;margin:0;}}
.container{{max-width:480px;margin:0 auto;background:#fff;border-radius:8px;padding:32px;border:1px solid #e4e4e7;}}
.logo{{font-size:22px;font-weight:700;text-align:center;margin-bottom:20px;color:#09090b;}}
.otp-box{{background:#f4f4f5;border-radius:6px;padding:20px;text-align:center;margin:24px 0;}}
.otp-code{{font-family:monospace;font-size:40px;font-weight:700;letter-spacing:0.2em;color:#09090b;}}
.expiry{{font-size:13px;color:#71717a;margin-top:8px;}}
.warning{{background:#fff1f2;border:1px solid #ffe4e6;border-radius:6px;padding:12px;color:#e11d48;font-size:12px;margin-top:16px;}}
.footer{{text-align:center;font-size:11px;color:#a1a1aa;margin-top:24px;}}
</style></head>
<body>
  <div class="container">
    <div class="logo">&#128274; Ollama Password Recovery</div>
    <p>Hello <strong>{name}</strong>,</p>
    <p>We received a request to reset your password. Use the OTP below to verify your identity.</p>
    <div class="otp-box">
      <div style="font-size:12px;text-transform:uppercase;letter-spacing:0.1em;color:#71717a;margin-bottom:8px;">One-Time Password</div>
      <div class="otp-code">{otp}</div>
      <div class="expiry">Valid for <strong>5 minutes</strong> only</div>
    </div>
    <div class="warning"><strong>&#9888;&#65039; Security Warning:</strong> Never share this OTP with anyone. Our team will never ask for it.</div>
    <p style="font-size:13px;color:#52525b;margin-top:16px;">If you did not request this, please ignore this email.</p>
    <div class="footer">&copy; 2026 Ollama Password Recovery Portal</div>
  </div>
</body>
</html>"""

    plain_body = (
        f"Hello {name},\n\n"
        f"Your OTP: {otp}\n\n"
        f"Valid for 5 minutes. Do not share this code with anyone.\n\n"
        f"Ollama Password Recovery Portal"
    )

    payload = json.dumps({
        "personalizations": [{"to": [{"email": to_email}]}],
        "from": {"email": mail_from},
        "subject": "Password Reset OTP — Ollama Recovery Portal",
        "content": [
            {"type": "text/plain", "value": plain_body},
            {"type": "text/html",  "value": html_body},
        ],
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://api.sendgrid.com/v3/mail/send",
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type":  "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req) as resp:
            print(f"[Email] OTP sent to {to_email}. HTTP {resp.status}")
            return True
    except urllib.error.HTTPError as e:
        err = e.read().decode()
        print(f"[Email] SendGrid error {e.code}: {err}")
        raise RuntimeError(f"Failed to send email: {err}")

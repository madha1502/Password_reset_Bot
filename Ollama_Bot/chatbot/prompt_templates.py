SYSTEM_PROMPT = """You are a helpful and secure IT Support Assistant specialising in password recovery \
for the Ollama Password Recovery Portal.

Your responsibilities:
- Guide users through the password reset process step by step
- Answer FAQs about account security and password management
- Troubleshoot common issues (OTP not received, expired OTP, login problems)
- Provide clear, concise, professional responses
- NEVER reveal, request, or guess passwords
- Keep answers friendly but brief (max 4 sentences or a short numbered list)

Password Reset Steps:
1. Visit the Forgot Password page
2. Enter your registered email address
3. Check your inbox for the 6-digit OTP (valid 5 minutes)
4. Enter the OTP on the Verify OTP page
5. Set your new password
6. Log in with your new credentials

Common OTP Issues:
- Expired OTP → request a new one from the Forgot Password page
- OTP not received → check Spam/Junk, verify correct email, wait 1-2 min
- Incorrect OTP → retype carefully, no extra spaces

Security Tips:
- Never share your OTP with anyone — not even support staff
- Use a strong password: mix of letters, numbers and symbols
- Each OTP is single-use and expires after 5 minutes"""


def build_messages(history: list, user_message: str) -> list:
    """Build the full message list for the Ollama /api/chat endpoint."""
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for entry in history[-10:]:          # keep last 10 turns for context
        messages.append({"role": entry["role"], "content": entry["message"]})
    messages.append({"role": "user", "content": user_message})
    return messages


# ─── Rule-based fallback (used when Ollama is offline) ───────────────────────

_FALLBACKS = {
    "forgot": (
        "Don't worry! Here's how to reset your password:\n"
        "1. Click **Forgot Password**\n"
        "2. Enter your registered email\n"
        "3. Check your inbox for the 6-digit OTP\n"
        "4. Enter the OTP to verify your identity\n"
        "5. Set your new password and log in"
    ),
    "otp": (
        "Your OTP is a 6-digit code sent to your registered email. "
        "It is valid for **5 minutes** and can only be used once. "
        "If it has expired, please request a new one from the Forgot Password page."
    ),
    "expired": (
        "Your OTP expired after 5 minutes. Go to **Forgot Password**, enter your email, "
        "and a fresh OTP will be sent to your inbox immediately."
    ),
    "not_received": (
        "If you didn't receive the OTP:\n"
        "1. Check your **Spam / Junk** folder\n"
        "2. Confirm you entered the correct email address\n"
        "3. Wait 1-2 minutes and refresh\n"
        "4. Click **Resend OTP** if still missing"
    ),
    "password_tips": (
        "A strong password should:\n"
        "• Be at least 8 characters long\n"
        "• Include uppercase and lowercase letters\n"
        "• Include numbers and special characters (@, #, $, etc.)\n"
        "• Never be shared with anyone"
    ),
    "default": (
        "I'm here to help with password recovery and account security. "
        "You can ask me about resetting your password, OTP issues, "
        "or general account security tips."
    ),
}


def get_fallback_response(user_message: str) -> str:
    """Return a rule-based response when Ollama is unavailable."""
    msg = user_message.lower()
    if any(w in msg for w in ["forgot", "reset", "recover", "lost", "can't login", "cant login", "unable to login"]):
        return _FALLBACKS["forgot"]
    if "expired" in msg:
        return _FALLBACKS["expired"]
    if any(w in msg for w in ["not received", "didn't receive", "no email", "not getting", "didn't get"]):
        return _FALLBACKS["not_received"]
    if any(w in msg for w in ["otp", "code", "verification", "verify"]):
        return _FALLBACKS["otp"]
    if any(w in msg for w in ["strong", "tip", "advice", "secure", "good password"]):
        return _FALLBACKS["password_tips"]
    return _FALLBACKS["default"]

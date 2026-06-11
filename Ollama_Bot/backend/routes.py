import hashlib
import secrets
import re
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, session
from backend.database import SessionLocal
from backend.models import User, OTPCode, AuditLog, ChatHistory

auth_bp  = Blueprint("auth",  __name__)
reset_bp = Blueprint("reset", __name__)
chat_bp  = Blueprint("chat",  __name__)
admin_bp = Blueprint("admin", __name__)

EMAIL_RE = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")


def _hash(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()

def _ip():
    return request.headers.get("X-Forwarded-For", request.remote_addr)

def _log(db, email, action):
    db.add(AuditLog(email=email, action=action, ip_address=_ip(), timestamp=datetime.utcnow()))
    db.commit()


# ─── AUTH ────────────────────────────────────────────────────────────────────

@auth_bp.post("/register")
def register():
    db = SessionLocal()
    try:
        d = request.get_json() or {}
        name     = d.get("name", "").strip()
        email    = d.get("email", "").strip().lower()
        password = d.get("password", "").strip()

        if not name:
            return jsonify({"error": "Name is required."}), 400
        if not EMAIL_RE.match(email):
            return jsonify({"error": "Invalid email address."}), 400
        if len(password) < 6:
            return jsonify({"error": "Password must be at least 6 characters."}), 400
        if db.query(User).filter(User.email == email).first():
            return jsonify({"error": "An account with this email already exists."}), 400

        db.add(User(name=name, email=email, password_hash=_hash(password)))
        db.commit()
        _log(db, email, "USER_REGISTERED")
        return jsonify({"message": "Account created successfully."}), 201
    finally:
        db.close()


@auth_bp.post("/login")
def login():
    db = SessionLocal()
    try:
        d = request.get_json() or {}
        email    = d.get("email", "").strip().lower()
        password = d.get("password", "").strip()

        user = db.query(User).filter(User.email == email).first()
        if not user or user.password_hash != _hash(password):
            _log(db, email or "unknown", "LOGIN_FAILED")
            return jsonify({"error": "Invalid email or password."}), 401

        session["user_id"]  = user.id
        session["email"]    = user.email
        session["name"]     = user.name
        session["is_admin"] = user.is_admin
        _log(db, email, "LOGIN_SUCCESS")
        return jsonify({"message": "Login successful.", "name": user.name, "is_admin": user.is_admin})
    finally:
        db.close()


@auth_bp.post("/logout")
def logout():
    email = session.get("email", "unknown")
    session.clear()
    db = SessionLocal()
    try:
        _log(db, email, "LOGOUT")
    finally:
        db.close()
    return jsonify({"message": "Logged out successfully."})


@auth_bp.get("/me")
def me():
    if "user_id" not in session:
        return jsonify({"error": "Not authenticated."}), 401
    return jsonify({"name": session["name"], "email": session["email"], "is_admin": session["is_admin"]})


# ─── PASSWORD RESET ──────────────────────────────────────────────────────────

@reset_bp.post("/forgot-password")
def forgot_password():
    from email_service.otp_mail import send_otp_email
    from risk_engine.analyzer import analyze_request

    db = SessionLocal()
    try:
        d = request.get_json() or {}
        email = d.get("email", "").strip().lower()

        if not EMAIL_RE.match(email):
            return jsonify({"error": "Invalid email address."}), 400

        user = db.query(User).filter(User.email == email).first()
        if not user:
            _log(db, email, "USER_NOT_FOUND")
            return jsonify({"error": "No account found with this email."}), 404

        risk = analyze_request(email, _ip(), db)
        if risk["level"] == "HIGH":
            return jsonify({"error": "Too many reset attempts. Please wait before trying again."}), 429

        otp = f"{secrets.randbelow(900000) + 100000}"
        expires_at = datetime.utcnow() + timedelta(minutes=5)
        db.add(OTPCode(email=email, otp=_hash(otp), expires_at=expires_at, is_used=False))
        db.commit()
        _log(db, email, "OTP_GENERATED")

        send_otp_email(email, otp, user.name)
        _log(db, email, "OTP_SENT")

        return jsonify({"message": "OTP sent to your email.", "risk_level": risk["level"]})
    finally:
        db.close()


@reset_bp.post("/verify-otp")
def verify_otp():
    db = SessionLocal()
    try:
        d = request.get_json() or {}
        email = d.get("email", "").strip().lower()
        otp   = d.get("otp", "").strip()

        record = (db.query(OTPCode)
                    .filter(OTPCode.email == email)
                    .order_by(OTPCode.created_at.desc())
                    .first())

        if not record:
            return jsonify({"error": "No OTP request found for this email."}), 400
        if record.is_used:
            return jsonify({"error": "This OTP has already been used."}), 400
        if record.expires_at < datetime.utcnow():
            return jsonify({"error": "OTP has expired. Please request a new one."}), 400
        if record.otp != _hash(otp):
            _log(db, email, "OTP_VERIFICATION_FAILED")
            return jsonify({"error": "Incorrect OTP."}), 400

        record.is_used = True
        session["otp_verified"] = True
        session["reset_email"]  = email
        db.commit()
        _log(db, email, "OTP_VERIFIED")
        return jsonify({"message": "OTP verified successfully.", "verified": True})
    finally:
        db.close()


@reset_bp.post("/reset-password")
def reset_password():
    db = SessionLocal()
    try:
        d = request.get_json() or {}
        email        = d.get("email", "").strip().lower()
        new_password = d.get("new_password", "").strip()

        if not session.get("otp_verified") or session.get("reset_email") != email:
            return jsonify({"error": "Unauthorized. Please verify your OTP first."}), 401
        if len(new_password) < 6:
            return jsonify({"error": "Password must be at least 6 characters."}), 400

        user = db.query(User).filter(User.email == email).first()
        if not user:
            return jsonify({"error": "User not found."}), 404

        user.password_hash = _hash(new_password)
        db.query(OTPCode).filter(OTPCode.email == email).delete()
        db.commit()

        session.pop("otp_verified", None)
        session.pop("reset_email", None)
        _log(db, email, "PASSWORD_RESET")
        return jsonify({"message": "Password reset successfully."})
    finally:
        db.close()


# ─── CHAT ────────────────────────────────────────────────────────────────────

@chat_bp.post("/message")
def chat_message():
    from chatbot.assistant import process_message
    d          = request.get_json() or {}
    message    = d.get("message", "").strip()
    session_id = d.get("session_id", "anonymous")

    if not message:
        return jsonify({"error": "Message cannot be empty."}), 400

    db = SessionLocal()
    try:
        response = process_message(session_id, message, db)
        return jsonify({"response": response, "session_id": session_id})
    finally:
        db.close()


@chat_bp.get("/history")
def chat_history():
    session_id = request.args.get("session_id", "anonymous")
    db = SessionLocal()
    try:
        rows = (db.query(ChatHistory)
                  .filter(ChatHistory.session_id == session_id)
                  .order_by(ChatHistory.timestamp.asc())
                  .all())
        return jsonify([{"role": r.role, "message": r.message, "timestamp": str(r.timestamp)} for r in rows])
    finally:
        db.close()


@chat_bp.delete("/history")
def clear_history():
    session_id = request.args.get("session_id", "anonymous")
    db = SessionLocal()
    try:
        db.query(ChatHistory).filter(ChatHistory.session_id == session_id).delete()
        db.commit()
        return jsonify({"message": "Chat history cleared."})
    finally:
        db.close()


# ─── ADMIN ───────────────────────────────────────────────────────────────────

@admin_bp.get("/dashboard")
def dashboard():
    from admin.dashboard import get_stats, get_recent_logs
    from admin.analytics import get_reset_trend, get_chat_stats
    db = SessionLocal()
    try:
        return jsonify({
            "stats":      get_stats(db),
            "logs":       get_recent_logs(db),
            "trend":      get_reset_trend(db),
            "chat_stats": get_chat_stats(db),
        })
    finally:
        db.close()


@admin_bp.get("/logs")
def all_logs():
    from admin.dashboard import get_recent_logs
    db = SessionLocal()
    try:
        return jsonify(get_recent_logs(db, limit=100))
    finally:
        db.close()

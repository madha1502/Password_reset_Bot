from datetime import datetime, timedelta
from backend.models import User, AuditLog, RiskLog, ChatHistory


def get_stats(db) -> dict:
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    return {
        "total_users":     db.query(User).count(),
        "resets_today":    db.query(AuditLog).filter(AuditLog.action == "PASSWORD_RESET",  AuditLog.timestamp >= today).count(),
        "otp_sent_today":  db.query(AuditLog).filter(AuditLog.action == "OTP_SENT",        AuditLog.timestamp >= today).count(),
        "high_risk_today": db.query(RiskLog).filter(RiskLog.risk_level == "HIGH",          RiskLog.timestamp  >= today).count(),
        "total_chats":     db.query(ChatHistory).count(),
    }


def get_recent_logs(db, limit: int = 50) -> list:
    rows = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(limit).all()
    return [
        {"id": r.id, "email": r.email, "action": r.action,
         "ip_address": r.ip_address, "timestamp": str(r.timestamp)}
        for r in rows
    ]

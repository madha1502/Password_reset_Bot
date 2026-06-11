from datetime import datetime, timedelta
from backend.models import AuditLog, ChatHistory


def get_reset_trend(db, days: int = 7) -> list:
    """Return OTP-sent counts per day for the last N days."""
    trend = []
    for i in range(days - 1, -1, -1):
        day      = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=i)
        next_day = day + timedelta(days=1)
        count    = db.query(AuditLog).filter(
            AuditLog.action == "OTP_SENT",
            AuditLog.timestamp >= day,
            AuditLog.timestamp <  next_day,
        ).count()
        trend.append({"date": day.strftime("%Y-%m-%d"), "count": count})
    return trend


def get_chat_stats(db) -> dict:
    total     = db.query(ChatHistory).count()
    user_msgs = db.query(ChatHistory).filter(ChatHistory.role == "user").count()
    return {
        "total_messages":     total,
        "user_messages":      user_msgs,
        "assistant_messages": total - user_msgs,
    }

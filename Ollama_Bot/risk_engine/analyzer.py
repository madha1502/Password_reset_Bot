from datetime import datetime, timedelta
from backend.models import AuditLog, RiskLog
from risk_engine.scoring import compute_risk


def analyze_request(email: str, ip: str, db) -> dict:
    """
    Analyse a password-reset request for suspicious activity.
    Persists a RiskLog record and returns the risk assessment dict.
    """
    one_hour_ago = datetime.utcnow() - timedelta(hours=1)

    # Count OTP requests for this email in the last hour
    request_count = (
        db.query(AuditLog)
        .filter(
            AuditLog.email == email,
            AuditLog.action == "OTP_GENERATED",
            AuditLog.timestamp >= one_hour_ago,
        )
        .count()
    )

    # Check if same IP targeted multiple accounts in the last hour
    ip_count = 0
    if ip:
        ip_count = (
            db.query(AuditLog)
            .filter(
                AuditLog.ip_address == ip,
                AuditLog.action == "OTP_GENERATED",
                AuditLog.timestamp >= one_hour_ago,
            )
            .count()
        )
    is_repeated_ip = ip_count >= 3

    risk = compute_risk(request_count, is_repeated_ip)

    # Persist risk log
    db.add(RiskLog(
        email=email,
        risk_level=risk["level"],
        reason=risk["reason"],
        score=risk["score"],
        timestamp=datetime.utcnow(),
    ))
    db.commit()

    print(f"[Risk] {email} → {risk['level']} (score={risk['score']})")
    return risk

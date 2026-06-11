def compute_risk(request_count: int, is_repeated_ip: bool = False) -> dict:
    """
    Compute risk level from reset frequency and IP patterns.
    Returns dict with keys: level (SAFE/MEDIUM/HIGH), score (float), reason (str).
    """
    score   = 0.0
    reasons = []

    if request_count >= 5:
        score += 80.0
        reasons.append(f"{request_count} reset attempts in the last hour")
    elif request_count >= 3:
        score += 40.0
        reasons.append(f"{request_count} reset attempts in the last hour")
    elif request_count >= 2:
        score += 20.0
        reasons.append(f"{request_count} reset attempts in the last hour")

    if is_repeated_ip:
        score += 15.0
        reasons.append("Multiple accounts targeted from the same IP")

    if score >= 70:
        level = "HIGH"
    elif score >= 25:
        level = "MEDIUM"
    else:
        level = "SAFE"

    return {
        "level":  level,
        "score":  round(score, 2),
        "reason": "; ".join(reasons) if reasons else "Normal activity",
    }

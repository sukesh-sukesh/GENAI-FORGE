"""
InsureGuard AI - Pattern Alerts Module
Detects suspicious patterns in claims data.
"""

from typing import Dict, Any, List
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.models.claim import Claim, ClaimStatus, RiskCategory
from app.models.user import User


def detect_rapid_claims(db: Session, days_window: int = 30) -> List[Dict[str, Any]]:
    """
    Detect users filing multiple claims within a short time window.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=days_window)

    # Get users with multiple recent claims
    rapid_claimants = db.query(
        Claim.user_id, func.count(Claim.id).label("claim_count")
    ).filter(
        Claim.created_at >= cutoff
    ).group_by(Claim.user_id).having(func.count(Claim.id) > 2).all()

    alerts = []
    for user_id, count in rapid_claimants:
        user = db.query(User).filter(User.id == user_id).first()
        recent_claims = db.query(Claim).filter(
            Claim.user_id == user_id,
            Claim.created_at >= cutoff
        ).order_by(desc(Claim.created_at)).all()

        total_amount = sum(c.claim_amount for c in recent_claims)

        alerts.append({
            "alert_type": "rapid_claims",
            "severity": "critical" if count > 4 else "high",
            "user_id": user_id,
            "user_name": user.full_name if user else "Unknown",
            "claim_count": count,
            "total_amount": total_amount,
            "time_window": f"{days_window} days",
            "message": f"User filed {count} claims in {days_window} days totaling ₹{total_amount:,.2f}"
        })

    return alerts


def detect_high_value_anomalies(db: Session) -> List[Dict[str, Any]]:
    """
    Detect claims with amounts significantly above category average.
    """
    alerts = []
    categories = ["vehicle", "health", "property"]

    for category in categories:
        avg_amount = db.query(func.avg(Claim.claim_amount)).filter(
            Claim.insurance_category == category
        ).scalar() or 0

        if avg_amount == 0:
            continue

        threshold = avg_amount * 3  # 3x average is suspicious

        high_claims = db.query(Claim).filter(
            Claim.insurance_category == category,
            Claim.claim_amount > threshold
        ).all()

        for claim in high_claims:
            alerts.append({
                "alert_type": "high_value_anomaly",
                "severity": "high",
                "claim_id": claim.id,
                "claim_number": claim.claim_number,
                "category": category,
                "claim_amount": claim.claim_amount,
                "category_average": round(avg_amount, 2),
                "multiplier": round(claim.claim_amount / avg_amount, 1),
                "message": f"Claim ₹{claim.claim_amount:,.2f} is {claim.claim_amount/avg_amount:.1f}x the {category} average"
            })

    return alerts


def detect_new_policy_claims(db: Session, days_threshold: int = 30) -> List[Dict[str, Any]]:
    """Detect claims filed very soon after policy start."""
    alerts = []

    claims = db.query(Claim).filter(
        Claim.policy_start_date.isnot(None),
        Claim.incident_date.isnot(None)
    ).all()

    for claim in claims:
        if claim.policy_start_date and claim.incident_date:
            days_diff = (claim.incident_date - claim.policy_start_date).days
            if 0 <= days_diff <= days_threshold:
                alerts.append({
                    "alert_type": "new_policy_claim",
                    "severity": "medium" if days_diff > 14 else "high",
                    "claim_id": claim.id,
                    "claim_number": claim.claim_number,
                    "days_since_policy_start": days_diff,
                    "message": f"Claim filed only {days_diff} days after policy start"
                })

    return alerts


def get_all_alerts(db: Session) -> Dict[str, Any]:
    """Get all fraud pattern alerts."""
    rapid = detect_rapid_claims(db)
    high_value = detect_high_value_anomalies(db)
    new_policy = detect_new_policy_claims(db)

    all_alerts = rapid + high_value + new_policy
    all_alerts.sort(key=lambda x: {"critical": 0, "high": 1, "medium": 2}.get(x["severity"], 3))

    return {
        "total_alerts": len(all_alerts),
        "critical_alerts": len([a for a in all_alerts if a["severity"] == "critical"]),
        "high_alerts": len([a for a in all_alerts if a["severity"] == "high"]),
        "medium_alerts": len([a for a in all_alerts if a["severity"] == "medium"]),
        "alerts": all_alerts
    }

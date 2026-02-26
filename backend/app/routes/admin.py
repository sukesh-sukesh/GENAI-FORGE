"""
InsureGuard AI - Admin Routes
Manager and admin-level endpoints for fraud intelligence.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.middleware.auth_middleware import require_manager, require_agent, get_current_user
from app.models.user import User
from app.models.claim import Claim, RiskCategory
from app.models.audit import AuditLog
from app.fraud_intelligence.entity_detection import detect_repeated_entities
from app.fraud_intelligence.network_detection import detect_fraud_networks
from app.fraud_intelligence.pattern_alerts import get_all_alerts
from app.schemas.claim import ClaimResponse
from app.config import FRAUD_THRESHOLD_LOW, FRAUD_THRESHOLD_HIGH

router = APIRouter(prefix="/api/admin", tags=["Admin"])


@router.get("/fraud-intelligence")
def get_fraud_intelligence(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager)
):
    """Get comprehensive fraud intelligence report."""
    entities = detect_repeated_entities(db)
    networks = detect_fraud_networks(db)
    alerts = get_all_alerts(db)

    return {
        "entities": entities,
        "networks": networks,
        "alerts": alerts
    }


@router.get("/alerts")
def get_alerts(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_agent)
):
    """Get fraud pattern alerts."""
    return get_all_alerts(db)


@router.get("/high-risk-claims")
def get_high_risk_claims(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_agent)
):
    """Get all high-risk flagged claims."""
    claims = db.query(Claim).filter(
        Claim.risk_category == RiskCategory.HIGH
    ).order_by(Claim.created_at.desc()).all()

    return {
        "total": len(claims),
        "claims": [ClaimResponse.model_validate(c) for c in claims]
    }


@router.get("/audit-logs")
def get_audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    action: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager)
):
    """Get audit logs (managers only)."""
    query = db.query(AuditLog)
    if action:
        query = query.filter(AuditLog.action == action)

    total = query.count()
    logs = query.order_by(AuditLog.created_at.desc()).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    return {
        "total": total,
        "page": page,
        "logs": [{
            "id": log.id,
            "user_id": log.user_id,
            "action": log.action,
            "resource_type": log.resource_type,
            "resource_id": log.resource_id,
            "details": log.details,
            "created_at": str(log.created_at)
        } for log in logs]
    }


@router.get("/thresholds")
def get_thresholds(current_user: User = Depends(require_manager)):
    """Get current fraud detection thresholds."""
    return {
        "low_threshold": FRAUD_THRESHOLD_LOW,
        "high_threshold": FRAUD_THRESHOLD_HIGH,
        "description": "Claims below low threshold = Low Risk, above high threshold = High Risk"
    }


@router.post("/thresholds")
def update_thresholds(
    low: float = Query(..., ge=0, le=1),
    high: float = Query(..., ge=0, le=1),
    current_user: User = Depends(require_manager)
):
    """Update fraud detection thresholds (in-memory, restart resets)."""
    import app.config as config
    config.FRAUD_THRESHOLD_LOW = low
    config.FRAUD_THRESHOLD_HIGH = high

    return {
        "message": "Thresholds updated successfully",
        "low_threshold": low,
        "high_threshold": high
    }

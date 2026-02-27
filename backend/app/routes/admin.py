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
from app.models.system_config import SystemConfig
from sqlalchemy import func
from datetime import date

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


@router.get("/risk-threshold")
def get_risk_threshold(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager)
):
    """Get dynamic risk threshold."""
    config = db.query(SystemConfig).first()
    if not config:
        config = SystemConfig()
        db.add(config)
        db.commit()
        db.refresh(config)
    return {"fraud_threshold": config.fraud_threshold, "avg_fraud_loss": config.avg_fraud_loss}


@router.put("/risk-threshold")
def update_risk_threshold(
    fraud_threshold: float,
    avg_fraud_loss: float = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager)
):
    """Update dynamic risk threshold."""
    config = db.query(SystemConfig).first()
    if not config:
        config = SystemConfig()
        db.add(config)
    config.fraud_threshold = fraud_threshold
    if avg_fraud_loss is not None:
        config.avg_fraud_loss = avg_fraud_loss
    db.commit()
    db.refresh(config)
    return {"message": "Threshold updated successfully", "fraud_threshold": config.fraud_threshold, "avg_fraud_loss": config.avg_fraud_loss}


@router.get("/business-impact")
def get_business_impact(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager)
):
    config = db.query(SystemConfig).first()
    avg_loss = config.avg_fraud_loss if config else 50000.0
    high_risk_claims = db.query(Claim).filter(Claim.risk_category == RiskCategory.HIGH).count()
    prevented_loss = high_risk_claims * avg_loss
    return {"prevented_loss": prevented_loss, "avg_fraud_loss": avg_loss, "high_risk_claims": high_risk_claims}


@router.get("/fraud-network")
def get_fraud_network(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager)
):
    claims = db.query(Claim).all()
    nodes = []
    edges = []
    node_set = set()
    
    for c in claims:
        ph = f"User_{c.user_id}"
        sh = c.repair_shop_name or "Unknown_Shop"
        
        if ph not in node_set:
            nodes.append({"id": ph, "label": ph, "group": "policyholder"})
            node_set.add(ph)
            
        if sh != "Unknown_Shop" and sh not in node_set:
            nodes.append({"id": sh, "label": sh, "group": "repair_shop"})
            node_set.add(sh)
            
        if sh != "Unknown_Shop":
            edges.append({"from": ph, "to": sh, "label": f"Claim {c.id}"})
            
    return {"nodes": nodes, "edges": edges}


@router.get("/timeline")
def get_timeline(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager)
):
    timeline = db.query(
        func.date(Claim.created_at).label('date'),
        func.count(Claim.id).label('total'),
        func.sum(func.case((Claim.risk_category == 'high', 1), else_=0)).label('high_risk')
    ).group_by(func.date(Claim.created_at)).all()
    
    result = []
    for row in timeline:
        total = row.total
        hr = row.high_risk or 0
        pct = (hr / total * 100) if total > 0 else 0
        result.append({
            "date": str(row.date),
            "total_claims": total,
            "high_risk_claims": hr,
            "fraud_percentage": round(pct, 2)
        })
    return result


@router.get("/ml-metrics")
def get_ml_metrics(
    current_user: User = Depends(require_manager)
):
    import json
    from app.config import ML_MODELS_DIR
    metadata_path = ML_MODELS_DIR / "model_metadata.json"
    if not metadata_path.exists():
        return {"error": "Model metadata not found"}
    with open(metadata_path, "r") as f:
        return json.load(f)

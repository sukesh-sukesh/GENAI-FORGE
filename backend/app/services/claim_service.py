"""
InsureGuard AI - Claim Service
Core business logic for claim submission, retrieval, and management.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from fastapi import HTTPException, status

from app.models.claim import Claim, ClaimStatus, InsuranceCategory, RiskCategory
from app.models.user import User
from app.models.audit import AuditLog
from app.schemas.claim import ClaimCreate, ClaimResponse, ClaimUpdate


def generate_claim_number(category: str) -> str:
    """Generate unique claim number: IG-VEH-2024-XXXX format."""
    prefix_map = {"vehicle": "VEH", "health": "HLT", "property": "PRP"}
    prefix = prefix_map.get(category, "GEN")
    uid = uuid.uuid4().hex[:8].upper()
    return f"IG-{prefix}-{datetime.now().year}-{uid}"


def submit_claim(db: Session, claim_data: ClaimCreate, user: User) -> ClaimResponse:
    """Submit a new insurance claim."""
    claim = Claim(
        claim_number=generate_claim_number(claim_data.insurance_category),
        user_id=user.id,
        insurance_category=InsuranceCategory(claim_data.insurance_category),
        policy_number=claim_data.policy_number,
        policy_start_date=claim_data.policy_start_date,
        premium_amount=claim_data.premium_amount,
        claim_amount=claim_data.claim_amount,
        incident_date=claim_data.incident_date,
        incident_description=claim_data.incident_description,
        incident_location=claim_data.incident_location,
        # Vehicle
        vehicle_number=claim_data.vehicle_number,
        vehicle_make_model=claim_data.vehicle_make_model,
        repair_shop_name=claim_data.repair_shop_name,
        repair_shop_address=claim_data.repair_shop_address,
        # Health
        hospital_name=claim_data.hospital_name,
        hospital_registration_number=claim_data.hospital_registration_number,
        diagnosis=claim_data.diagnosis,
        treatment_type=claim_data.treatment_type,
        admission_date=claim_data.admission_date,
        discharge_date=claim_data.discharge_date,
        # Property
        property_type=claim_data.property_type,
        property_address=claim_data.property_address,
        damage_type=claim_data.damage_type,
        property_ownership_type=claim_data.property_ownership_type,
        additional_data=claim_data.additional_data,
        status=ClaimStatus.PENDING
    )

    db.add(claim)
    db.commit()
    db.refresh(claim)

    # Audit
    log = AuditLog(user_id=user.id, action="claim_submitted",
                   resource_type="claim", resource_id=claim.id,
                   details={"claim_number": claim.claim_number,
                            "category": claim_data.insurance_category})
    db.add(log)
    db.commit()

    return ClaimResponse.model_validate(claim)


def get_claim(db: Session, claim_id: int, user: User) -> ClaimResponse:
    """Get a single claim by ID."""
    claim = db.query(Claim).filter(Claim.id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")

    # Users can only see their own claims
    if user.role.value == "user" and claim.user_id != user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    return ClaimResponse.model_validate(claim)


def get_claims(
    db: Session,
    user: User,
    page: int = 1,
    page_size: int = 20,
    status_filter: Optional[str] = None,
    category_filter: Optional[str] = None,
    risk_filter: Optional[str] = None,
    search: Optional[str] = None
) -> Dict[str, Any]:
    """Get paginated list of claims with filters."""
    query = db.query(Claim)

    # Users see only their claims; agents/managers see all
    if user.role.value == "user":
        query = query.filter(Claim.user_id == user.id)

    if status_filter:
        query = query.filter(Claim.status == ClaimStatus(status_filter))

    if category_filter:
        query = query.filter(Claim.insurance_category == InsuranceCategory(category_filter))

    if risk_filter:
        query = query.filter(Claim.risk_category == RiskCategory(risk_filter))

    if search:
        query = query.filter(
            (Claim.claim_number.ilike(f"%{search}%")) |
            (Claim.policy_number.ilike(f"%{search}%"))
        )

    total = query.count()
    claims = query.order_by(desc(Claim.created_at)).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    return {
        "claims": [ClaimResponse.model_validate(c) for c in claims],
        "total": total,
        "page": page,
        "page_size": page_size
    }


def update_claim_decision(
    db: Session, claim_id: int, update_data: ClaimUpdate, user: User
) -> ClaimResponse:
    """Update claim status and decision."""
    claim = db.query(Claim).filter(Claim.id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")

    if update_data.status:
        claim.status = ClaimStatus(update_data.status)
    if update_data.decision_notes:
        claim.decision_notes = update_data.decision_notes
    if update_data.assigned_agent_id:
        claim.assigned_agent_id = update_data.assigned_agent_id

    claim.decided_by = user.id
    claim.decided_at = datetime.now(timezone.utc)
    claim.updated_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(claim)

    # Audit
    log = AuditLog(user_id=user.id, action=f"claim_{update_data.status or 'updated'}",
                   resource_type="claim", resource_id=claim.id,
                   details={"status": update_data.status,
                            "notes": update_data.decision_notes})
    db.add(log)
    db.commit()

    return ClaimResponse.model_validate(claim)


def get_analytics(db: Session) -> Dict[str, Any]:
    """Generate claim analytics for dashboards."""
    total = db.query(Claim).count()

    # Status counts
    status_counts = {}
    for s in ClaimStatus:
        status_counts[s.value] = db.query(Claim).filter(Claim.status == s).count()

    # Risk counts
    risk_counts = {}
    for r in RiskCategory:
        risk_counts[r.value] = db.query(Claim).filter(Claim.risk_category == r).count()

    # Category counts
    cat_counts = {}
    for c in InsuranceCategory:
        cat_counts[c.value] = db.query(Claim).filter(Claim.insurance_category == c).count()

    # Average fraud probability
    avg_fraud = db.query(func.avg(Claim.fraud_probability)).filter(
        Claim.fraud_probability.isnot(None)
    ).scalar() or 0

    # Fraud trend (last 30 days grouped by date)
    from datetime import timedelta
    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
    recent_claims = db.query(Claim).filter(
        Claim.created_at >= thirty_days_ago
    ).order_by(Claim.created_at).all()

    fraud_trend = []
    daily_data = {}
    for claim in recent_claims:
        date_key = claim.created_at.strftime("%Y-%m-%d") if claim.created_at else "unknown"
        if date_key not in daily_data:
            daily_data[date_key] = {"date": date_key, "total": 0, "high_risk": 0, "avg_score": 0, "scores": []}
        daily_data[date_key]["total"] += 1
        if claim.risk_category and claim.risk_category.value == "high":
            daily_data[date_key]["high_risk"] += 1
        if claim.fraud_probability:
            daily_data[date_key]["scores"].append(claim.fraud_probability)

    for date_key, data in sorted(daily_data.items()):
        avg = sum(data["scores"]) / len(data["scores"]) if data["scores"] else 0
        fraud_trend.append({
            "date": data["date"],
            "total_claims": data["total"],
            "high_risk_claims": data["high_risk"],
            "avg_fraud_probability": round(avg, 3)
        })

    # Recent claims
    latest = db.query(Claim).order_by(desc(Claim.created_at)).limit(10).all()

    return {
        "total_claims": total,
        "pending_claims": status_counts.get("pending", 0),
        "approved_claims": status_counts.get("approved", 0),
        "rejected_claims": status_counts.get("rejected", 0),
        "escalated_claims": status_counts.get("escalated", 0),
        "high_risk_claims": risk_counts.get("high", 0),
        "medium_risk_claims": risk_counts.get("medium", 0),
        "low_risk_claims": risk_counts.get("low", 0),
        "average_fraud_probability": round(float(avg_fraud), 3),
        "claims_by_category": cat_counts,
        "claims_by_status": status_counts,
        "fraud_trend": fraud_trend,
        "recent_claims": [ClaimResponse.model_validate(c) for c in latest]
    }

"""
InsureGuard AI - Claims Routes
CRUD operations for insurance claims with fraud prediction.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.schemas.claim import ClaimCreate, ClaimResponse, ClaimUpdate
from app.services.claim_service import (
    submit_claim, get_claim, get_claims, update_claim_decision, get_analytics
)
from app.middleware.auth_middleware import get_current_user, require_agent, require_manager
from app.models.user import User
from app.models.claim import Claim
from app.ml.risk_scoring import predict_fraud_risk, compute_shap_explanations
from app.document_verification.validator import validate_documents_for_category

router = APIRouter(prefix="/api/claims", tags=["Claims"])


@router.post("/", response_model=ClaimResponse)
def create_claim(
    claim_data: ClaimCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Submit a new insurance claim."""
    claim_response = submit_claim(db, claim_data, current_user)

    # Run fraud prediction
    try:
        # Count user's existing claims
        user_claims_count = db.query(Claim).filter(
            Claim.user_id == current_user.id
        ).count()

        # Get dynamic threshold
        from app.models.system_config import SystemConfig
        config = db.query(SystemConfig).first()
        threshold = config.fraud_threshold if config else 0.70

        claim_dict = claim_data.model_dump()
        risk_result = predict_fraud_risk(claim_dict, user_claims_count, fraud_threshold=threshold)

        # Update claim with risk assessment
        claim = db.query(Claim).filter(Claim.id == claim_response.id).first()
        if claim:
            claim.fraud_probability = risk_result["fraud_probability"]
            claim.risk_score = risk_result["risk_score"]
            claim.risk_category = risk_result["risk_category"]
            claim.fraud_factors = risk_result["fraud_factors"]
            claim.anomaly_score = risk_result.get("anomaly_score")

            # SHAP explanations
            shap_vals = compute_shap_explanations(claim_dict, user_claims_count)
            claim.shap_values = shap_vals

            # Document validation
            doc_validation = validate_documents_for_category(
                claim_data.insurance_category, [], claim_dict
            )
            claim.document_verification_details = doc_validation

            # Auto-escalate high risk
            if risk_result["risk_category"] == "high":
                claim.status = "escalated"

            db.commit()
            db.refresh(claim)
            claim_response = ClaimResponse.model_validate(claim)

            # Add Fraud Pattern Alerts
            try:
                from app.models.fraud_alert import FraudAlert
                from datetime import timedelta
                from sqlalchemy import func
                
                # Rule 1: Same repair shop >=3 claims in 48h
                if claim.repair_shop_name:
                    recent_time = claim.created_at - timedelta(hours=48)
                    shop_claims = db.query(Claim).filter(
                        Claim.repair_shop_name == claim.repair_shop_name,
                        Claim.created_at >= recent_time
                    ).count()
                    if shop_claims >= 3:
                        alert = FraudAlert(
                            claim_id=claim.id,
                            alert_type="frequent_repair_shop",
                            description=f"Repair shop {claim.repair_shop_name} used in >=3 claims within 48 hours",
                            severity="High"
                        )
                        db.add(alert)
                        
                # Rule 2: Claim amount > 2x category average
                avg_amt = db.query(func.avg(Claim.claim_amount)).filter(Claim.insurance_category == claim.insurance_category).scalar()
                if avg_amt and claim.claim_amount > (2 * avg_amt):
                    alert = FraudAlert(
                        claim_id=claim.id,
                        alert_type="high_claim_amount",
                        description=f"Claim amount > 2x average for category",
                        severity="Medium"
                    )
                    db.add(alert)
                    
                # Rule 3: Claim within 7 days of policy start
                if claim.policy_start_date and claim.incident_date:
                    days_diff = (claim.incident_date - claim.policy_start_date).days
                    if 0 <= days_diff <= 7:
                        alert = FraudAlert(
                            claim_id=claim.id,
                            alert_type="early_claim",
                            description=f"Claim filed within {days_diff} days of policy start",
                            severity="High"
                        )
                        db.add(alert)
                        
                # Rule 4: Same phone across multiple policies
                if current_user.phone:
                    from app.models.user import User
                    distinct_policies = db.query(func.count(func.distinct(Claim.policy_number)))\
                        .join(User, Claim.user_id == User.id)\
                        .filter(User.phone == current_user.phone)\
                        .scalar()
                        
                    if distinct_policies and distinct_policies > 1:
                        alert = FraudAlert(
                            claim_id=claim.id,
                            alert_type="shared_phone",
                            description=f"Phone number {current_user.phone} linked to {distinct_policies} different policies",
                            severity="High"
                        )
                        db.add(alert)
                db.commit()
            except Exception as e:
                print(f"Warning: Fraud alerts failed: {e}")

    except Exception as e:
        print(f"Warning: Fraud prediction failed: {e}")

    return claim_response


@router.get("/", response_model=dict)
def list_claims(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    category: Optional[str] = None,
    risk: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get paginated list of claims with filters."""
    return get_claims(db, current_user, page, page_size, status, category, risk, search)


@router.get("/analytics", response_model=dict)
def claim_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_agent)
):
    """Get claim analytics (agents and managers only)."""
    return get_analytics(db)


@router.get("/{claim_id}", response_model=ClaimResponse)
def get_single_claim(
    claim_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific claim by ID."""
    return get_claim(db, claim_id, current_user)


@router.put("/{claim_id}", response_model=ClaimResponse)
def update_claim(
    claim_id: int,
    update_data: ClaimUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_agent)
):
    """Update claim status and decision (agents/managers only)."""
    return update_claim_decision(db, claim_id, update_data, current_user)


@router.post("/{claim_id}/predict", response_model=dict)
def predict_claim_risk(
    claim_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_agent)
):
    """Re-run fraud prediction on a claim (agents/managers only)."""
    claim = db.query(Claim).filter(Claim.id == claim_id).first()
    if not claim:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Claim not found")

    user_claims_count = db.query(Claim).filter(Claim.user_id == claim.user_id).count()

    claim_dict = {
        "insurance_category": claim.insurance_category.value if claim.insurance_category else "vehicle",
        "claim_amount": claim.claim_amount,
        "premium_amount": claim.premium_amount,
        "policy_start_date": claim.policy_start_date,
        "incident_date": claim.incident_date,
        "incident_description": claim.incident_description or "",
        "incident_location": claim.incident_location,
        "repair_shop_name": claim.repair_shop_name,
        "vehicle_number": claim.vehicle_number,
        "hospital_name": claim.hospital_name,
        "admission_date": claim.admission_date,
        "discharge_date": claim.discharge_date,
        "created_at": claim.created_at
    }

    # Get dynamic threshold
    from app.models.system_config import SystemConfig
    config = db.query(SystemConfig).first()
    threshold = config.fraud_threshold if config else 0.70

    risk_result = predict_fraud_risk(claim_dict, user_claims_count, fraud_threshold=threshold)

    # Update claim
    claim.fraud_probability = risk_result["fraud_probability"]
    claim.risk_score = risk_result["risk_score"]
    claim.risk_category = risk_result["risk_category"]
    claim.fraud_factors = risk_result["fraud_factors"]
    db.commit()

    return {
        "fraud_probability": risk_result["fraud_probability"],
        "risk_level": risk_result["risk_level"],
        "confidence_score": risk_result["confidence_score"],
        "key_risk_factors": risk_result["key_risk_factors"]
    }


@router.post("/{claim_id}/label")
def add_claim_label(
    claim_id: int,
    label: str = Query(..., pattern="^(genuine|fraud)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_agent)
):
    """Mark claim as Confirmed Fraud or Genuine."""
    from datetime import datetime, timezone
    claim = db.query(Claim).filter(Claim.id == claim_id).first()
    if not claim:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Claim not found")
        
    claim.reviewer_label = label
    claim.reviewed_at = datetime.now(timezone.utc)
    claim.reviewed_by = current_user.id
    db.commit()
    return {"message": f"Claim {claim_id} marked as {label}"}


@router.get("/{claim_id}/report")
def download_claim_report(
    claim_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate and return a lightweight PDF report."""
    from fastapi.responses import FileResponse
    from fpdf import FPDF
    import tempfile
    import os
    from app.models.fraud_alert import FraudAlert

    claim = db.query(Claim).filter(Claim.id == claim_id).first()
    if not claim:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Claim not found")
        
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    
    pdf.cell(200, 10, txt="Investigation Report", ln=1, align="C")
    pdf.cell(200, 10, txt=f"Claim Number: {claim.claim_number}", ln=1)
    pdf.cell(200, 10, txt=f"Category: {claim.insurance_category.value.title()}", ln=1)
    pdf.cell(200, 10, txt=f"Risk Score: {claim.risk_score} - {str(claim.risk_category).title()}", ln=1)
    
    if claim.anomaly_score is not None:
        pdf.cell(200, 10, txt=f"Anomaly Score: {claim.anomaly_score}", ln=1)
        
    pdf.cell(200, 10, txt="", ln=1)
    pdf.cell(200, 10, txt="Top Factors:", ln=1)
    if claim.fraud_factors:
        if isinstance(claim.fraud_factors, dict) and "positive_factors" in claim.fraud_factors:
            all_factors = claim.fraud_factors.get("positive_factors", []) + claim.fraud_factors.get("negative_factors", [])
            for factor in sorted(all_factors, key=lambda x: x.get('weight_pct', 0), reverse=True)[:5]:
                pdf.cell(200, 10, txt=f"- {factor.get('feature')}: {factor.get('contribution')}", ln=1)
        elif isinstance(claim.fraud_factors, list):
            for factor in claim.fraud_factors[:5]:
                pdf.cell(200, 10, txt=f"- {factor.get('feature')}: {factor.get('contribution')}", ln=1)
            
    pdf.cell(200, 10, txt="", ln=1)
    alerts = db.query(FraudAlert).filter(FraudAlert.claim_id == claim.id).all()
    if alerts:
        pdf.cell(200, 10, txt="Triggered Alerts:", ln=1)
        for a in alerts:
            pdf.cell(200, 10, txt=f"- {a.severity} [{a.alert_type}]: {a.description}", ln=1)
            
    fd, path = tempfile.mkstemp(suffix=".pdf")
    os.close(fd)
    pdf.output(path)
    return FileResponse(path, filename=f"Claim_{claim.claim_number}_Report.pdf")


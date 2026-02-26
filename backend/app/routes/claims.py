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

        claim_dict = claim_data.model_dump()
        risk_result = predict_fraud_risk(claim_dict, user_claims_count)

        # Update claim with risk assessment
        claim = db.query(Claim).filter(Claim.id == claim_response.id).first()
        if claim:
            claim.fraud_probability = risk_result["fraud_probability"]
            claim.risk_score = risk_result["risk_score"]
            claim.risk_category = risk_result["risk_category"]
            claim.fraud_factors = risk_result["fraud_factors"]

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

    risk_result = predict_fraud_risk(claim_dict, user_claims_count)

    # Update claim
    claim.fraud_probability = risk_result["fraud_probability"]
    claim.risk_score = risk_result["risk_score"]
    claim.risk_category = risk_result["risk_category"]
    claim.fraud_factors = risk_result["fraud_factors"]
    db.commit()

    return risk_result

"""
InsureGuard AI - Claim Schemas
Pydantic models for claim submission and responses.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class ClaimCreate(BaseModel):
    insurance_category: str = Field(..., pattern=r"^(vehicle|health|property)$")
    policy_number: str = Field(..., min_length=5)
    policy_start_date: Optional[datetime] = None
    premium_amount: Optional[float] = Field(None, ge=0)
    claim_amount: float = Field(..., gt=0)
    incident_date: datetime
    incident_description: str = Field(..., min_length=10)
    incident_location: Optional[str] = None

    # Vehicle-specific
    vehicle_number: Optional[str] = None
    vehicle_make_model: Optional[str] = None
    repair_shop_name: Optional[str] = None
    repair_shop_address: Optional[str] = None

    # Health-specific
    hospital_name: Optional[str] = None
    hospital_registration_number: Optional[str] = None
    diagnosis: Optional[str] = None
    treatment_type: Optional[str] = None
    admission_date: Optional[datetime] = None
    discharge_date: Optional[datetime] = None

    # Property-specific
    property_type: Optional[str] = None
    property_address: Optional[str] = None
    damage_type: Optional[str] = None
    property_ownership_type: Optional[str] = None

    additional_data: Optional[Dict[str, Any]] = None


class RiskAssessment(BaseModel):
    fraud_probability: float = Field(..., ge=0, le=1)
    risk_score: float = Field(..., ge=0, le=100)
    risk_category: str
    fraud_factors: List[Dict[str, Any]] = []
    shap_values: Optional[Dict[str, Any]] = None


class ClaimResponse(BaseModel):
    id: int
    claim_number: str
    user_id: int
    insurance_category: str
    policy_number: str
    claim_amount: float
    incident_date: Optional[datetime] = None
    incident_description: str
    incident_location: Optional[str] = None
    status: str
    fraud_probability: Optional[float] = None
    risk_score: Optional[float] = None
    risk_category: Optional[str] = None
    fraud_factors: Optional[List[Dict[str, Any]]] = None
    shap_values: Optional[Dict[str, Any]] = None
    document_verification_status: Optional[str] = None
    document_verification_details: Optional[Dict[str, Any]] = None
    decision_notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # Category-specific fields
    vehicle_number: Optional[str] = None
    vehicle_make_model: Optional[str] = None
    repair_shop_name: Optional[str] = None
    hospital_name: Optional[str] = None
    diagnosis: Optional[str] = None
    property_type: Optional[str] = None
    damage_type: Optional[str] = None
    additional_data: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class ClaimUpdate(BaseModel):
    status: Optional[str] = Field(None, pattern=r"^(pending|under_review|approved|rejected|escalated)$")
    decision_notes: Optional[str] = None
    assigned_agent_id: Optional[int] = None


class ClaimListResponse(BaseModel):
    claims: List[ClaimResponse]
    total: int
    page: int
    page_size: int


class AnalyticsResponse(BaseModel):
    total_claims: int
    pending_claims: int
    approved_claims: int
    rejected_claims: int
    escalated_claims: int
    high_risk_claims: int
    medium_risk_claims: int
    low_risk_claims: int
    average_fraud_probability: float
    claims_by_category: Dict[str, int]
    claims_by_status: Dict[str, int]
    fraud_trend: List[Dict[str, Any]]
    recent_claims: List[ClaimResponse]

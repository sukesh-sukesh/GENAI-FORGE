"""
InsureGuard AI - Claim Model
Supports Vehicle, Health, and Property insurance claims with full tracking.
"""

from sqlalchemy import (Column, Integer, String, Float, DateTime, Text,
                         ForeignKey, JSON, Boolean, Enum as SQLEnum)
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import enum

from app.database import Base


class InsuranceCategory(str, enum.Enum):
    VEHICLE = "vehicle"
    HEALTH = "health"
    PROPERTY = "property"


class ClaimStatus(str, enum.Enum):
    PENDING = "pending"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    ESCALATED = "escalated"


class RiskCategory(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Claim(Base):
    __tablename__ = "claims"

    id = Column(Integer, primary_key=True, index=True)
    claim_number = Column(String(50), unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    assigned_agent_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Insurance Details
    insurance_category = Column(SQLEnum(InsuranceCategory), nullable=False)
    policy_number = Column(String(50), nullable=False)
    policy_start_date = Column(DateTime, nullable=True)
    premium_amount = Column(Float, nullable=True)
    claim_amount = Column(Float, nullable=False)
    incident_date = Column(DateTime, nullable=False)
    incident_description = Column(Text, nullable=False)
    incident_location = Column(String(500), nullable=True)

    # Vehicle-specific fields
    vehicle_number = Column(String(20), nullable=True)
    vehicle_make_model = Column(String(100), nullable=True)
    repair_shop_name = Column(String(200), nullable=True)
    repair_shop_address = Column(String(500), nullable=True)

    # Health-specific fields
    hospital_name = Column(String(200), nullable=True)
    hospital_registration_number = Column(String(50), nullable=True)
    diagnosis = Column(String(500), nullable=True)
    treatment_type = Column(String(100), nullable=True)
    admission_date = Column(DateTime, nullable=True)
    discharge_date = Column(DateTime, nullable=True)

    # Property-specific fields
    property_type = Column(String(100), nullable=True)
    property_address = Column(String(500), nullable=True)
    damage_type = Column(String(200), nullable=True)
    property_ownership_type = Column(String(50), nullable=True)

    # Risk Assessment
    fraud_probability = Column(Float, nullable=True)  # 0-1
    risk_score = Column(Float, nullable=True)          # 0-100
    risk_category = Column(SQLEnum(RiskCategory), nullable=True)
    fraud_factors = Column(JSON, nullable=True)        # Top contributing factors
    shap_values = Column(JSON, nullable=True)          # SHAP explanations

    # Status & Decision
    status = Column(SQLEnum(ClaimStatus), default=ClaimStatus.PENDING)
    decision_notes = Column(Text, nullable=True)
    decided_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    decided_at = Column(DateTime, nullable=True)

    # Document Verification
    document_verification_status = Column(String(50), default="pending")
    document_verification_details = Column(JSON, nullable=True)

    # Metadata
    additional_data = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    user = relationship("User", back_populates="claims", foreign_keys=[user_id])
    assigned_agent = relationship("User", back_populates="assigned_claims",
                                  foreign_keys=[assigned_agent_id])
    documents = relationship("ClaimDocument", back_populates="claim",
                             cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Claim {self.claim_number} ({self.insurance_category})>"


class ClaimDocument(Base):
    __tablename__ = "claim_documents"

    id = Column(Integer, primary_key=True, index=True)
    claim_id = Column(Integer, ForeignKey("claims.id"), nullable=False)
    document_type = Column(String(100), nullable=False)  # rc_copy, fir_copy, hospital_bill, etc.
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=True)
    mime_type = Column(String(100), nullable=True)
    file_hash = Column(String(64), nullable=True)  # SHA256 hash for duplicate detection

    # Verification
    is_verified = Column(Boolean, default=False)
    verification_details = Column(JSON, nullable=True)
    ocr_text = Column(Text, nullable=True)

    # Metadata
    uploaded_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    claim = relationship("Claim", back_populates="documents")

    def __repr__(self):
        return f"<ClaimDocument {self.document_type} for claim {self.claim_id}>"

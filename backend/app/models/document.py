"""
InsureGuard AI - Document Verification Model
Tracks document validation results.
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, JSON, Boolean, ForeignKey
from datetime import datetime, timezone

from app.database import Base


class DocumentVerification(Base):
    __tablename__ = "document_verifications"

    id = Column(Integer, primary_key=True, index=True)
    claim_document_id = Column(Integer, ForeignKey("claim_documents.id"), nullable=False)
    claim_id = Column(Integer, ForeignKey("claims.id"), nullable=False)

    # OCR Results
    ocr_confidence = Column(Float, nullable=True)
    extracted_text = Column(Text, nullable=True)
    extracted_data = Column(JSON, nullable=True)  # Structured data from OCR

    # Validation Results
    format_valid = Column(Boolean, nullable=True)
    gst_number_valid = Column(Boolean, nullable=True)
    gst_number_extracted = Column(String(20), nullable=True)
    rc_number_valid = Column(Boolean, nullable=True)
    rc_number_extracted = Column(String(20), nullable=True)
    hospital_reg_valid = Column(Boolean, nullable=True)
    invoice_format_valid = Column(Boolean, nullable=True)

    # Cross-check Results
    amount_match = Column(Boolean, nullable=True)
    amount_on_document = Column(Float, nullable=True)
    policy_number_match = Column(Boolean, nullable=True)

    # Image Analysis
    is_duplicate = Column(Boolean, default=False)
    duplicate_of_document_id = Column(Integer, nullable=True)
    metadata_suspicious = Column(Boolean, default=False)
    metadata_details = Column(JSON, nullable=True)

    # Overall
    verification_score = Column(Float, nullable=True)  # 0-100
    verification_status = Column(String(50), default="pending")
    notes = Column(Text, nullable=True)

    verified_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

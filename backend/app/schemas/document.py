"""
InsureGuard AI - Document Schemas
"""

from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime


class DocumentResponse(BaseModel):
    id: int
    claim_id: int
    document_type: str
    file_name: str
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    is_verified: bool = False
    verification_details: Optional[Dict[str, Any]] = None
    uploaded_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DocumentVerificationResponse(BaseModel):
    document_id: int
    ocr_confidence: Optional[float] = None
    format_valid: Optional[bool] = None
    gst_number_valid: Optional[bool] = None
    rc_number_valid: Optional[bool] = None
    amount_match: Optional[bool] = None
    is_duplicate: bool = False
    verification_score: Optional[float] = None
    verification_status: str
    notes: Optional[str] = None

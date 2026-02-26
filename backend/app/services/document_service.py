"""
InsureGuard AI - Document Service
Handles file uploads, duplicate detection, and document management.
"""

import hashlib
import shutil
from pathlib import Path
from typing import List
from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session

from app.config import UPLOAD_DIR, ALLOWED_EXTENSIONS, MAX_FILE_SIZE_MB
from app.models.claim import Claim, ClaimDocument
from app.models.audit import AuditLog
from app.models.user import User


def get_file_hash(file_content: bytes) -> str:
    """Calculate SHA256 hash of file content."""
    return hashlib.sha256(file_content).hexdigest()


async def upload_document(
    db: Session,
    claim_id: int,
    document_type: str,
    file: UploadFile,
    user: User
) -> dict:
    """Upload a document for a claim."""
    # Verify claim exists and belongs to user
    claim = db.query(Claim).filter(Claim.id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    if user.role.value == "user" and claim.user_id != user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    # Validate file extension
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # Read file content
    content = await file.read()

    # Check file size
    if len(content) > MAX_FILE_SIZE_MB * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum: {MAX_FILE_SIZE_MB}MB"
        )

    # Calculate hash for duplicate detection
    file_hash = get_file_hash(content)

    # Check for duplicate documents across all claims
    duplicate = db.query(ClaimDocument).filter(
        ClaimDocument.file_hash == file_hash
    ).first()

    is_duplicate = duplicate is not None

    # Save file
    claim_dir = UPLOAD_DIR / str(claim_id)
    claim_dir.mkdir(parents=True, exist_ok=True)
    file_path = claim_dir / f"{document_type}_{file.filename}"

    with open(file_path, "wb") as f:
        f.write(content)

    # Create document record
    doc = ClaimDocument(
        claim_id=claim_id,
        document_type=document_type,
        file_name=file.filename,
        file_path=str(file_path),
        file_size=len(content),
        mime_type=file.content_type,
        file_hash=file_hash
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    # Audit
    log = AuditLog(
        user_id=user.id, action="document_uploaded",
        resource_type="document", resource_id=doc.id,
        details={"claim_id": claim_id, "document_type": document_type,
                 "is_duplicate": is_duplicate}
    )
    db.add(log)
    db.commit()

    return {
        "id": doc.id,
        "claim_id": claim_id,
        "document_type": document_type,
        "file_name": file.filename,
        "file_size": len(content),
        "is_duplicate": is_duplicate,
        "duplicate_claim_id": duplicate.claim_id if duplicate else None,
        "message": "Document uploaded successfully" + (
            " (WARNING: Duplicate detected!)" if is_duplicate else ""
        )
    }


def get_claim_documents(db: Session, claim_id: int) -> List[dict]:
    """Get all documents for a claim."""
    docs = db.query(ClaimDocument).filter(ClaimDocument.claim_id == claim_id).all()
    return [{
        "id": d.id,
        "claim_id": d.claim_id,
        "document_type": d.document_type,
        "file_name": d.file_name,
        "file_size": d.file_size,
        "mime_type": d.mime_type,
        "is_verified": d.is_verified,
        "verification_details": d.verification_details,
        "uploaded_at": str(d.uploaded_at) if d.uploaded_at else None
    } for d in docs]


# Required documents per category
REQUIRED_DOCUMENTS = {
    "vehicle": ["rc_copy", "driving_license", "fir_copy", "damage_images", "repair_estimate"],
    "health": ["hospital_bill", "discharge_summary", "prescription", "id_proof"],
    "property": ["damage_images", "police_report", "ownership_proof", "cost_estimation"]
}


def check_required_documents(db: Session, claim_id: int, category: str) -> dict:
    """Check if all required documents are uploaded."""
    docs = db.query(ClaimDocument).filter(ClaimDocument.claim_id == claim_id).all()
    uploaded_types = {d.document_type for d in docs}
    required = set(REQUIRED_DOCUMENTS.get(category, []))

    missing = required - uploaded_types
    return {
        "complete": len(missing) == 0,
        "required": list(required),
        "uploaded": list(uploaded_types),
        "missing": list(missing)
    }

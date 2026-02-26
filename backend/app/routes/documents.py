"""
InsureGuard AI - Document Routes
File upload and document verification endpoints.
"""

from fastapi import APIRouter, Depends, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth_middleware import get_current_user
from app.models.user import User
from app.services.document_service import (
    upload_document, get_claim_documents, check_required_documents
)

router = APIRouter(prefix="/api/documents", tags=["Documents"])


@router.post("/upload")
async def upload_doc(
    claim_id: int = Form(...),
    document_type: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Upload a document for a claim."""
    return await upload_document(db, claim_id, document_type, file, current_user)


@router.get("/claim/{claim_id}")
def get_documents(
    claim_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all documents for a claim."""
    return get_claim_documents(db, claim_id)


@router.get("/check/{claim_id}/{category}")
def check_documents(
    claim_id: int,
    category: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Check if required documents are uploaded for a category."""
    return check_required_documents(db, claim_id, category)

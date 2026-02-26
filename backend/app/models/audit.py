"""
InsureGuard AI - Audit Log Model
Tracks all actions for compliance and security.
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, ForeignKey
from datetime import datetime, timezone

from app.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String(100), nullable=False)  # e.g., "claim_submitted", "claim_approved"
    resource_type = Column(String(50), nullable=True)  # e.g., "claim", "document"
    resource_id = Column(Integer, nullable=True)
    details = Column(JSON, nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<AuditLog {self.action} by user {self.user_id}>"

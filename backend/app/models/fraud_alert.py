"""
InsureGuard AI - Fraud Alert Model
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from datetime import datetime, timezone

from app.database import Base

class FraudAlert(Base):
    __tablename__ = "fraud_alerts"

    id = Column(Integer, primary_key=True, index=True)
    claim_id = Column(Integer, ForeignKey("claims.id"), nullable=False)
    alert_type = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    severity = Column(String(50), nullable=False) # Low, Medium, High
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<FraudAlert {self.alert_type} for claim {self.claim_id}>"

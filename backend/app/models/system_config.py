"""
InsureGuard AI - System Config Model
"""
from sqlalchemy import Column, Integer, Float

from app.database import Base

class SystemConfig(Base):
    __tablename__ = "system_config"

    id = Column(Integer, primary_key=True, index=True)
    fraud_threshold = Column(Float, default=0.70)
    avg_fraud_loss = Column(Float, default=50000.0)

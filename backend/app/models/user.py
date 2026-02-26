"""
InsureGuard AI - User Model
Supports role-based access: user, agent, manager
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import enum

from app.database import Base


class UserRole(str, enum.Enum):
    USER = "user"
    AGENT = "agent"
    MANAGER = "manager"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    phone = Column(String(15), nullable=True)
    role = Column(SQLEnum(UserRole), default=UserRole.USER, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    claims = relationship("Claim", back_populates="user", foreign_keys="Claim.user_id")
    assigned_claims = relationship("Claim", back_populates="assigned_agent",
                                   foreign_keys="Claim.assigned_agent_id")

    def __repr__(self):
        return f"<User {self.email} ({self.role})>"

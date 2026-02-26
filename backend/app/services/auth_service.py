"""
InsureGuard AI - Authentication Service
Handles user registration, login, and token management.
"""

from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UserLogin, UserResponse, TokenResponse
from app.middleware.auth_middleware import hash_password, verify_password, create_access_token
from app.models.audit import AuditLog


def register_user(db: Session, user_data: UserCreate) -> UserResponse:
    """Register a new user."""
    # Check if email already exists
    existing = db.query(User).filter(User.email == user_data.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    user = User(
        email=user_data.email,
        full_name=user_data.full_name,
        hashed_password=hash_password(user_data.password),
        phone=user_data.phone,
        role=UserRole(user_data.role)
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Audit log
    log = AuditLog(user_id=user.id, action="user_registered",
                   resource_type="user", resource_id=user.id)
    db.add(log)
    db.commit()

    return UserResponse.model_validate(user)


def login_user(db: Session, login_data: UserLogin) -> TokenResponse:
    """Authenticate user and return JWT token."""
    user = db.query(User).filter(User.email == login_data.email).first()
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated"
        )

    token = create_access_token(data={"sub": str(user.id), "role": user.role.value})

    # Audit log
    log = AuditLog(user_id=user.id, action="user_login",
                   resource_type="user", resource_id=user.id)
    db.add(log)
    db.commit()

    return TokenResponse(
        access_token=token,
        user=UserResponse.model_validate(user)
    )

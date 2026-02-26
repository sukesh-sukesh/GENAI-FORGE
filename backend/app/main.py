"""
InsureGuard AI - Main Application
AI-Powered General Insurance Fraud Detection & Claim Risk Intelligence System
For the Indian Insurance Market

Version: 1.0.0
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os

from app.config import APP_NAME, APP_VERSION, CORS_ORIGINS, UPLOAD_DIR
from app.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    # Startup
    print(f"[*] Starting {APP_NAME} v{APP_VERSION}...")
    init_db()
    print("[OK] Database initialized")

    # Train ML model if not exists
    from app.config import ML_MODELS_DIR
    model_path = ML_MODELS_DIR / "fraud_model.joblib"
    if not model_path.exists():
        print("[ML] Training fraud detection model...")
        from app.ml.model_training import train_and_compare_models
        train_and_compare_models()
        print("[OK] Model trained and saved")
    else:
        print("[OK] ML model loaded")

    # Seed default users if DB is empty
    _seed_default_users()

    yield

    # Shutdown
    print(f"[*] Shutting down {APP_NAME}")


def _seed_default_users():
    """Create default agent and manager accounts if they don't exist."""
    from app.database import SessionLocal
    from app.models.user import User, UserRole
    from app.middleware.auth_middleware import hash_password

    db = SessionLocal()
    try:
        # Check if any users exist
        if db.query(User).count() == 0:
            print("[SEED] Seeding default users...")

            users = [
                User(
                    email="admin@insureguard.in",
                    full_name="System Administrator",
                    hashed_password=hash_password("admin123"),
                    role=UserRole.MANAGER,
                    phone="9876543210"
                ),
                User(
                    email="agent@insureguard.in",
                    full_name="Claims Agent",
                    hashed_password=hash_password("agent123"),
                    role=UserRole.AGENT,
                    phone="9876543211"
                ),
                User(
                    email="user@insureguard.in",
                    full_name="Demo Policyholder",
                    hashed_password=hash_password("user123"),
                    role=UserRole.USER,
                    phone="9876543212"
                ),
            ]

            for u in users:
                db.add(u)
            db.commit()
            print(f"[OK] Created {len(users)} default users")

            # Seed some demo claims
            _seed_demo_claims(db)
    finally:
        db.close()


def _seed_demo_claims(db):
    """Create demo claims for showcasing the dashboard."""
    from app.models.claim import Claim, ClaimStatus, InsuranceCategory, RiskCategory
    from datetime import datetime, timedelta, timezone
    import random

    print("[SEED] Seeding demo claims...")

    categories = [
        ("vehicle", InsuranceCategory.VEHICLE),
        ("health", InsuranceCategory.HEALTH),
        ("property", InsuranceCategory.PROPERTY)
    ]

    statuses = list(ClaimStatus)
    risk_cats = list(RiskCategory)

    descriptions = {
        "vehicle": [
            "Front bumper damaged in rear-end collision on NH-48 highway",
            "Vehicle theft reported from parking lot in Mumbai, Andheri",
            "Windshield cracked due to flying debris on expressway",
            "Side mirror damaged in hit-and-run incident",
            "Total loss due to flood damage in monsoon season",
            "Engine damage from waterlogging on Mumbai roads",
            "Paint scratch from minor parking lot incident",
        ],
        "health": [
            "Emergency appendectomy surgery at Apollo Hospital",
            "Cardiac stent placement procedure - 3 stents required",
            "Knee replacement surgery after sports injury",
            "Hospitalization for dengue fever, 5-day ICU stay",
            "Cataract surgery for both eyes over two sessions",
            "Treatment for fractured leg from road accident",
            "Pregnancy and delivery - caesarean section",
        ],
        "property": [
            "House damage due to severe flooding in Kerala",
            "Fire damage to kitchen and living room areas",
            "Roof collapse after cyclone Biparjoy in Gujarat",
            "Burglary resulting in loss of valuables and electronics",
            "Water damage from burst pipes in apartment building",
            "Structural damage from earthquake in Maharashtra",
            "Storm damage to commercial property roof and windows",
        ],
    }

    locations = [
        "Mumbai, Maharashtra", "Delhi NCR", "Bangalore, Karnataka",
        "Hyderabad, Telangana", "Chennai, Tamil Nadu", "Pune, Maharashtra",
        "Kolkata, West Bengal", "Ahmedabad, Gujarat", "Jaipur, Rajasthan",
        "Kochi, Kerala", "Lucknow, Uttar Pradesh", "Noida, UP",
    ]

    shops = ["AutoCare Express", "QuickFix Motors", "RoadStar Repairs",
             "City Auto Works", "Prime Car Service", None, None]

    hospitals = ["Apollo Hospital", "Fortis Healthcare", "Max Super Specialty",
                 "AIIMS", "Narayana Health", "Medanta", None]

    for i in range(25):
        cat_name, cat_enum = random.choice(categories)
        status = random.choice(statuses)
        risk = random.choice(risk_cats)
        fraud_prob = random.uniform(0.05, 0.95)
        risk_score = fraud_prob * 100

        if risk == RiskCategory.LOW:
            fraud_prob = random.uniform(0.05, 0.29)
        elif risk == RiskCategory.MEDIUM:
            fraud_prob = random.uniform(0.3, 0.69)
        else:
            fraud_prob = random.uniform(0.7, 0.95)

        risk_score = round(fraud_prob * 100, 1)

        claim_amount = random.choice([
            random.uniform(5000, 50000),
            random.uniform(50000, 200000),
            random.uniform(200000, 1000000),
            random.uniform(1000000, 5000000),
        ])

        days_ago = random.randint(1, 60)
        created = datetime.now(timezone.utc) - timedelta(days=days_ago)
        incident = created - timedelta(days=random.randint(0, 10))
        policy_start = incident - timedelta(days=random.randint(30, 730))

        claim = Claim(
            claim_number=f"IG-{cat_name[:3].upper()}-2024-{random.randint(10000,99999)}",
            user_id=random.choice([1, 3, 3, 3]),
            insurance_category=cat_enum,
            policy_number=f"POL-{random.randint(100000, 999999)}",
            policy_start_date=policy_start,
            premium_amount=random.uniform(5000, 50000),
            claim_amount=round(claim_amount, 2),
            incident_date=incident,
            incident_description=random.choice(descriptions[cat_name]),
            incident_location=random.choice(locations),
            vehicle_number=f"MH-{random.randint(1,50):02d}-AB-{random.randint(1000,9999)}" if cat_name == "vehicle" else None,
            vehicle_make_model=random.choice(["Maruti Swift", "Hyundai i20", "Tata Nexon", "Honda City", None]) if cat_name == "vehicle" else None,
            repair_shop_name=random.choice(shops) if cat_name == "vehicle" else None,
            hospital_name=random.choice(hospitals) if cat_name == "health" else None,
            diagnosis=random.choice(["Fracture", "Cardiac", "Surgery", "Infection", None]) if cat_name == "health" else None,
            property_type=random.choice(["Residential", "Commercial", "Industrial", None]) if cat_name == "property" else None,
            damage_type=random.choice(["Fire", "Flood", "Storm", "Theft", None]) if cat_name == "property" else None,
            fraud_probability=round(fraud_prob, 4),
            risk_score=risk_score,
            risk_category=risk,
            fraud_factors=[
                {"feature": "claim_to_premium_ratio", "value": round(random.uniform(1, 15), 2),
                 "contribution": round(random.uniform(0.1, 0.5), 3),
                 "description": "Claim-to-premium ratio exceeds normal range"},
                {"feature": "claim_frequency", "value": random.randint(1, 5),
                 "contribution": round(random.uniform(0.05, 0.3), 3),
                 "description": "Multiple claims filed by the same policyholder"},
                {"feature": "time_since_policy_start", "value": random.randint(10, 300),
                 "contribution": round(random.uniform(0.02, 0.2), 3),
                 "description": "Policy is very new"},
            ],
            status=status,
            created_at=created,
            updated_at=created,
            assigned_agent_id=2 if status != ClaimStatus.PENDING else None
        )

        db.add(claim)

    db.commit()
    print(f"[OK] Created 25 demo claims")


# Create FastAPI app
app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description="AI-Powered General Insurance Fraud Detection & Claim Risk Intelligence System for the Indian Market",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
from app.routes.auth import router as auth_router
from app.routes.claims import router as claims_router
from app.routes.documents import router as documents_router
from app.routes.admin import router as admin_router

app.include_router(auth_router)
app.include_router(claims_router)
app.include_router(documents_router)
app.include_router(admin_router)


# Serve frontend static files
import os
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "frontend")

@app.get("/api/info")
def root_info():
    return {
        "name": APP_NAME,
        "version": APP_VERSION,
        "status": "running"
    }

app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")


@app.get("/api/health")
def health_check():
    return {"status": "healthy", "service": APP_NAME}

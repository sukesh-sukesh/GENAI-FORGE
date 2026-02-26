"""
InsureGuard AI - Configuration Module
Handles all application configuration via environment variables.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR = BASE_DIR / "uploads"
ML_MODELS_DIR = BASE_DIR / "ml_models"
REPORTS_DIR = BASE_DIR / "reports"

# Create directories if they don't exist
for d in [UPLOAD_DIR, ML_MODELS_DIR, REPORTS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# Database
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR}/insureguard.db")

# JWT Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "insureguard-secret-key-change-in-production-2024")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "720"))

# Application
APP_NAME = "InsureGuard AI"
APP_VERSION = "1.0.0"
DEBUG = os.getenv("DEBUG", "true").lower() == "true"
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")

# File Upload
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "10"))
ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".bmp"}

# ML Configuration
FRAUD_THRESHOLD_LOW = float(os.getenv("FRAUD_THRESHOLD_LOW", "0.3"))
FRAUD_THRESHOLD_HIGH = float(os.getenv("FRAUD_THRESHOLD_HIGH", "0.7"))
MODEL_RETRAIN_INTERVAL_HOURS = int(os.getenv("MODEL_RETRAIN_INTERVAL_HOURS", "24"))

# Cost-Sensitive Learning
FALSE_NEGATIVE_COST = float(os.getenv("FALSE_NEGATIVE_COST", "10.0"))  # Cost of missing fraud
FALSE_POSITIVE_COST = float(os.getenv("FALSE_POSITIVE_COST", "1.0"))   # Cost of flagging genuine

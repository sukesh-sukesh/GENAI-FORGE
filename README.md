# 🛡️ InsureGuard AI

## AI-Powered General Insurance Fraud Detection & Claim Risk Intelligence System

> **For the Indian Insurance Market** | Vehicle • Health • Property Insurance

![Python](https://img.shields.io/badge/Python-3.11+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green)
![ML](https://img.shields.io/badge/ML-XGBoost%20|%20RandomForest-orange)
![License](https://img.shields.io/badge/License-MIT-purple)

---

## 🌟 Features

### 🎯 AI & ML Pipeline
- Multi-model fraud detection (Logistic Regression, Random Forest, XGBoost, Gradient Boosting)
- Automated model comparison with ROC-AUC, Precision-Recall, F1 optimization
- Cost-sensitive learning with customizable FN/FP costs
- SMOTE for class imbalance handling
- **14 engineered fraud-detection features**
- Explainable AI with top-5 contributing factor breakdown

### 📋 Multi-Category Support
- **Vehicle Insurance**: RC validation, repair shop tracking, FIR processing
- **Health Insurance**: Hospital bill verification, GST validation, treatment tracking
- **Property Insurance**: Damage assessment, ownership verification, cost estimation

### 🔍 Document Verification
- Indian document format validation (GST, PAN, Aadhaar, Vehicle RC)
- Amount cross-checking (form vs. document)
- SHA256-based duplicate image detection
- EXIF metadata tampering analysis

### 🕵️ Fraud Intelligence
- Repeated entity detection (phone, address, repair shop, hospital)
- Graph-based fraud network detection using DFS clustering
- Pattern alerts (rapid claims, high-value anomalies, new-policy claims)

### 🎨 Premium Dashboard
- Glassmorphism dark-mode UI
- Role-based dashboards (User, Agent, Manager)
- Interactive Chart.js visualizations
- Multi-step claim submission form
- Real-time risk gauge with SHAP explanations

### 🔒 Security
- JWT authentication with role-based access control
- Secure file upload with extension/size validation
- Input sanitization
- Comprehensive audit logging
- Indian insurance compliance standards

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- pip

### 1. Clone & Setup

```bash
cd GENAI_FORGE
cd backend
pip install -r requirements.txt
```

### 2. Start the Backend

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

On first run, the system will:
- Initialize the SQLite database
- Train the ML fraud detection model
- Seed demo users and 25 sample claims

### 3. Open the Frontend

Open `frontend/index.html` in your browser, or serve it:

```bash
cd frontend
python -m http.server 3000
```

Visit: http://localhost:3000

### 4. Demo Credentials

| Role | Email | Password |
|------|-------|----------|
| **Manager** | admin@insureguard.in | admin123 |
| **Agent** | agent@insureguard.in | agent123 |
| **User** | user@insureguard.in | user123 |

---

## 🐳 Docker Deployment

```bash
docker-compose up --build
```

- Backend: http://localhost:8000
- Frontend: http://localhost:3000
- API Docs: http://localhost:8000/api/docs

---

## 📁 Project Structure

```
GENAI_FORGE/
├── backend/
│   ├── app/
│   │   ├── main.py                    # FastAPI application
│   │   ├── config.py                  # Configuration
│   │   ├── database.py                # Database setup
│   │   ├── models/                    # SQLAlchemy models
│   │   │   ├── user.py                # User with RBAC
│   │   │   ├── claim.py               # Multi-category claims
│   │   │   ├── document.py            # Document verification
│   │   │   └── audit.py               # Audit logging
│   │   ├── schemas/                   # Pydantic schemas
│   │   ├── routes/                    # API endpoints
│   │   │   ├── auth.py                # Auth routes
│   │   │   ├── claims.py              # CRUD + fraud prediction
│   │   │   ├── documents.py           # File upload
│   │   │   └── admin.py               # Admin/manager routes
│   │   ├── services/                  # Business logic
│   │   ├── ml/                        # ML pipeline
│   │   │   ├── feature_engineering.py # 14 fraud features
│   │   │   ├── model_training.py      # Multi-model trainer
│   │   │   └── risk_scoring.py        # Risk assessment engine
│   │   ├── document_verification/     # OCR & validation
│   │   │   ├── validator.py           # Indian doc formats
│   │   │   └── image_analysis.py      # Duplicate detection
│   │   └── fraud_intelligence/        # Fraud detection
│   │       ├── entity_detection.py    # Repeated entity finder
│   │       ├── network_detection.py   # Graph-based networks
│   │       └── pattern_alerts.py      # Anomaly detection
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/
│   ├── index.html
│   ├── css/styles.css                 # Premium dark theme
│   └── js/
│       ├── config.js                  # App config
│       ├── api.js                     # API service
│       ├── auth.js                    # Authentication
│       ├── components.js              # Reusable UI
│       ├── dashboard.js               # Dashboards
│       ├── claims.js                  # Claim management
│       ├── admin.js                   # Admin pages
│       ├── manager.js                 # Manager pages
│       └── app.js                     # Router
├── docker-compose.yml
├── nginx.conf
└── README.md
```

---

## 🔌 API Endpoints

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | /api/auth/register | Register user | Public |
| POST | /api/auth/login | Login | Public |
| GET | /api/auth/me | Get profile | All |
| POST | /api/claims/ | Submit claim | All |
| GET | /api/claims/ | List claims | All |
| GET | /api/claims/{id} | Get claim | All |
| PUT | /api/claims/{id} | Update claim | Agent+ |
| POST | /api/claims/{id}/predict | Re-run AI | Agent+ |
| GET | /api/claims/analytics | Analytics | Agent+ |
| POST | /api/documents/upload | Upload doc | All |
| GET | /api/documents/claim/{id} | Get docs | All |
| GET | /api/admin/fraud-intelligence | Fraud intel | Manager |
| GET | /api/admin/alerts | Alerts | Agent+ |
| GET | /api/admin/high-risk-claims | High risk | Agent+ |
| GET | /api/admin/audit-logs | Audit trail | Manager |
| GET | /api/admin/thresholds | Get config | Manager |
| POST | /api/admin/thresholds | Update config | Manager |

Full Swagger docs: http://localhost:8000/api/docs

---

## 🤖 ML Model Details

### Features Used (14)
1. **claim_amount** — Raw claim amount
2. **premium_amount** — Policy premium
3. **claim_to_premium_ratio** — Claim/premium ratio (high = suspicious)
4. **time_since_policy_start** — Days from policy start to incident
5. **claim_frequency** — Number of claims by same user
6. **suspicious_amount_flag** — Above category threshold
7. **incident_severity** — NLP-based severity scoring
8. **location_risk** — Geo-based fraud probability
9. **weekend_holiday_flag** — Weekend/holiday incident
10. **late_reporting_flag** — Filed > 30 days after incident
11. **repair_shop_repetition** — Same shop across claims
12. **is_vehicle_claim** — Category one-hot
13. **is_health_claim** — Category one-hot
14. **is_property_claim** — Category one-hot

### Cost-Sensitive Optimization
- False Negative Cost (missed fraud): 10x
- False Positive Cost (false alarm): 1x
- Threshold optimized to minimize total business cost

---

## 📜 License

This project is for educational and demonstration purposes.
Built as a showcase of AI-powered insurance fraud detection for the Indian market.

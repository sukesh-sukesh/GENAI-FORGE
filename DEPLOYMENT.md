# 🚀 InsureGuard AI — Deployment Guide

## Table of Contents
1. [Local Development](#local-development)
2. [Docker Deployment](#docker-deployment)
3. [Production Deployment](#production-deployment)
4. [Environment Variables](#environment-variables)
5. [Database Migration](#database-migration)

---

## Local Development

### Prerequisites
- Python 3.11+
- pip
- Modern web browser (Chrome, Firefox, Edge)

### Setup

```bash
# 1. Navigate to the project
cd GENAI_FORGE

# 2. Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# 3. Install dependencies
cd backend
pip install -r requirements.txt

# 4. Start the backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 5. Serve the frontend (new terminal)
cd ../frontend
python -m http.server 3000
```

### Access Points
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **Swagger Docs**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc

---

## Docker Deployment

### Quick Start
```bash
docker-compose up --build -d
```

### Verify
```bash
docker-compose ps
docker-compose logs -f backend
```

### Stop
```bash
docker-compose down
```

---

## Production Deployment

### Option 1: Render.com

1. Push to GitHub
2. Create a new Web Service on Render
3. Set build command: `pip install -r backend/requirements.txt`
4. Set start command: `cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Set environment variables

### Option 2: Railway

1. Connect GitHub repo
2. Railway will auto-detect Python
3. Set start command in Procfile
4. Configure environment variables

### Option 3: AWS / GCP / Azure

1. Use Docker deployment
2. Push image to container registry
3. Deploy using ECS/Cloud Run/AKS
4. Configure load balancer and SSL

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| DATABASE_URL | sqlite:///./insureguard.db | Database connection string |
| SECRET_KEY | (random) | JWT signing key — CHANGE IN PRODUCTION |
| ACCESS_TOKEN_EXPIRE_MINUTES | 720 | Token expiry (12 hours) |
| DEBUG | true | Debug mode |
| CORS_ORIGINS | * | Allowed CORS origins |
| MAX_FILE_SIZE_MB | 10 | Max upload file size |
| FRAUD_THRESHOLD_LOW | 0.3 | Low risk threshold |
| FRAUD_THRESHOLD_HIGH | 0.7 | High risk threshold |
| FALSE_NEGATIVE_COST | 10.0 | Cost of missing fraud |
| FALSE_POSITIVE_COST | 1.0 | Cost of false alarm |

---

## Database Migration

### SQLite (Development)
Database is auto-created on first run. No migration needed.

### PostgreSQL (Production)
1. Update DATABASE_URL: `postgresql://user:pass@host:5432/insureguard`
2. Install psycopg2: `pip install psycopg2-binary`
3. Tables are auto-created by SQLAlchemy on startup

---

## Security Checklist

- [ ] Change SECRET_KEY to a strong random value
- [ ] Set DEBUG=false in production
- [ ] Use HTTPS (SSL/TLS)
- [ ] Restrict CORS_ORIGINS to your domain
- [ ] Use PostgreSQL instead of SQLite
- [ ] Set up proper backup procedures
- [ ] Configure rate limiting
- [ ] Enable logging and monitoring

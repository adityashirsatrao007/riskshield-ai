# RiskShield AI

[![CI](https://github.com/adityashirsatrao007/riskshield-ai/actions/workflows/ci.yml/badge.svg)](https://github.com/adityashirsatrao007/riskshield-ai/actions/workflows/ci.yml)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**Track 2 — AI Risk Manager** | Razorpay AI Buildathon 2026

> Real-time payment fraud detection for merchants. When a customer pays via Razorpay, RiskShield auto-scores the transaction using an ML model, flags suspicious payments, and alerts the merchant — all before the money settles.

## Live Demo Flow

```
Customer pays ₹499 → Razorpay checkout → Webhook fires → RiskShield scores → Alert if fraud
```

1. Customer opens the [Demo Page](http://localhost:3000/demo.html) and pays via Razorpay
2. Razorpay sends a `payment.captured` webhook to RiskShield
3. RiskShield's ML model scores the transaction in real-time
4. If flagged → alert created, merchant notified
5. Everything visible on the [Dashboard](http://localhost:3000) and [Grafana](http://localhost:3001)

## Architecture

```
                         Razorpay Checkout
                              │
                              ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────────┐
│   Frontend   │────▶│   Backend    │────▶│   ML Model       │
│  React/Vite  │     │   FastAPI    │     │  RandomForest    │
│  Port 3000   │     │  Port 8000   │     │  34 features     │
│              │     │              │     │  0.982 AUC-ROC   │
│  Demo Page   │     │  Webhooks    │     └──────────────────┘
│  /demo.html  │     │  Scoring     │
└──────────────┘     └──────┬───────┘
                            │
              ┌─────────────┼─────────────┐
              ▼             ▼             ▼
        ┌──────────┐  ┌──────────┐  ┌──────────┐
        │PostgreSQL│  │  Redis   │  │  Kafka   │
        │  Port    │  │  Port    │  │  Port    │
        │  5432    │  │  6380    │  │  9092    │
        └──────────┘  └──────────┘  └──────────┘
              │
     ┌────────┼────────────┐
     ▼        ▼            ▼
┌────────┐ ┌──────────┐ ┌──────────┐
│Grafana │ │Prometheus│ │ MLflow   │
│Port    │ │Port      │ │Port      │
│3001    │ │9090      │ │5000      │
└────────┘ └──────────┘ └──────────┘
```

### How It Works

1. Merchant sends transaction data via REST API, or Razorpay sends a webhook on payment capture
2. Risk engine extracts 34 features from transaction payload
3. RandomForest model computes fraud probability (0–1)
4. Risk level assigned: low (<0.3), medium (0.3–0.6), high (0.6–0.8), critical (≥0.86)
5. High-risk transactions automatically generate alerts
6. Top-5 feature importances provided as explainability (XAI)
7. Dashboard shows real-time monitoring, alerts, and analytics
8. Grafana panels visualize predictions, risk distribution, latency, and drift

### ML Model

- **Algorithm**: RandomForest Classifier (300 trees, max_depth=15)
- **Training Data**: [Kaggle Credit Card Fraud Dataset](https://www.kaggle.com/datasets/mlg-ulb/creditcardfraud) — 284,807 transactions, 0.17% fraud rate
- **Features**: 34 total — 28 PCA components (V1–V28) + Time + Amount + 4 derived (amount_log, amount_zscore, hour_of_day, is_high_amount)
- **Threshold**: 0.8631 (tuned for high precision on imbalanced data)

**Metrics** (on held-out test set):

| Metric | Value |
|--------|-------|
| AUC-ROC | 0.982 |
| F1 Score | 0.747 |
| Precision | 0.661 |
| Recall | 0.857 |

The PCA features come from dimensionality reduction applied to the original transaction attributes by the dataset authors. Our risk engine approximates these features from merchant-provided transaction metadata (amount, time, risk signals) and augments them with derived features for better discrimination.

### Explainability (XAI)

Every scoring decision returns the top-5 feature importances, so merchants understand *why* a transaction was flagged:

```json
{
  "explanations": [
    {"feature": "V14", "value": -4.21, "importance": 0.18, "description": "V14 = -4.21"},
    {"feature": "V10", "value": -3.87, "importance": 0.13, "description": "V10 = -3.87"},
    {"feature": "V12", "value": -2.94, "importance": 0.09, "description": "V12 = -2.94"}
  ]
}
```

### Risk Signals Evaluated

The risk engine considers these merchant-provided signals when computing features:

- **Transaction amount** — high amounts increase fraud probability
- **Account age** — new accounts (<7 days) are higher risk
- **Device fingerprint reuse** — same device across multiple accounts
- **Shipping address mismatch** — delivery address differs from billing
- **Transaction velocity** — low historical transaction count
- **International transactions** — cross-border payments carry higher risk
- **Time of day** — late-night transactions (0–5 AM) are riskier

### Key Features

- Real-time risk scoring with XAI explanations
- Razorpay integration (order creation, payment verification, webhook handling)
- Demo page with live Razorpay checkout → fraud scoring flow
- Alert management (acknowledge/dismiss/resolve)
- Batch transaction scoring
- API key + JWT authentication
- Prometheus metrics + Grafana dashboards (9 panels)
- MLflow experiment tracking
- Model drift detection (PSI monitoring)
- PCI DSS compliant (card numbers masked, never logged)
- PostgreSQL with async SQLAlchemy
- Docker multi-stage build with non-root user
- CI/CD pipeline (GitHub Actions)

## Quick Start

### Prerequisites
- Docker & Docker Compose

### Docker (Recommended)

```bash
git clone https://github.com/adityashirsatrao007/riskshield-ai.git
cd riskshield-ai
docker compose up --build
```

### Local Development

```bash
# Backend
cd backend
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000

# Frontend (new terminal)
cd frontend
npm install
npm run dev
```

## Services

| Service | Port | URL | Description |
|---------|------|-----|-------------|
| Frontend | 3000 | http://localhost:3000 | React dashboard |
| Demo Page | 3000 | http://localhost:3000/demo.html | Razorpay checkout demo |
| Backend API | 8000 | http://localhost:8000 | FastAPI REST API |
| Swagger Docs | 8000 | http://localhost:8000/docs | API documentation |
| Grafana | 3001 | http://localhost:3001 | Monitoring dashboard (admin/admin) |
| Prometheus | 9090 | http://localhost:9090 | Metrics collection |
| MLflow | 5000 | http://localhost:5000 | Experiment tracking |
| PostgreSQL | 5432 | localhost:5432 | Database |
| Redis | 6380 | localhost:6380 | Cache & sessions |
| Kafka | 9092 | localhost:9092 | Event streaming |

## API

All merchant endpoints require `X-API-Key` header. Admin endpoints require the admin API key.

### Register a Merchant
```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name": "Acme Corp", "email": "dev@acme.com"}'
```

### Score a Transaction
```bash
curl -X POST http://localhost:8000/api/v1/transactions \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_MERCHANT_API_KEY" \
  -d '{
    "transaction_id": "TXN001",
    "amount": 45000,
    "currency": "INR",
    "merchant_id": "M001",
    "customer_id": "C001",
    "card_number": "4111111111111111",
    "is_international": true,
    "customer_account_age_days": 3,
    "customer_total_transactions": 1,
    "shipping_address_match": false,
    "device_fingerprint_reused": true
  }'
```

### Response
```json
{
  "success": true,
  "data": {
    "transaction_id": "TXN001",
    "risk_score": 0.87,
    "risk_level": "critical",
    "is_flagged": true,
    "explanations": [
      {"feature": "V14", "value": -4.21, "importance": 0.18, "description": "V14 = -4.21"},
      {"feature": "V10", "value": -3.87, "importance": 0.13, "description": "V10 = -3.87"},
      {"feature": "V17", "value": 3.12, "importance": 0.09, "description": "V17 = 3.12"}
    ],
    "processing_time_ms": 12.5
  }
}
```

### Razorpay Integration

```bash
# Create order
curl -X POST http://localhost:8000/api/v1/orders \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ADMIN_API_KEY" \
  -d '{"amount": 499, "currency": "INR"}'

# Verify payment
curl -X POST http://localhost:8000/api/v1/orders/verify \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ADMIN_API_KEY" \
  -d '{
    "razorpay_order_id": "order_xxx",
    "razorpay_payment_id": "pay_xxx",
    "razorpay_signature": "xxx"
  }'
```

### Other Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/v1/auth/register` | None | Register merchant, get API key |
| POST | `/api/v1/auth/login` | API Key | Get JWT token |
| GET | `/api/v1/auth/me` | JWT | Current merchant info |
| POST | `/api/v1/transactions` | API Key | Score single transaction |
| POST | `/api/v1/transactions/batch` | API Key | Batch score transactions |
| GET | `/api/v1/transactions` | API Key | List transactions |
| POST | `/api/v1/orders` | Admin | Create Razorpay order |
| POST | `/api/v1/orders/verify` | Admin | Verify Razorpay payment |
| GET | `/api/v1/alerts` | Admin | List alerts |
| PUT | `/api/v1/alerts/{id}/status` | Admin | Update alert status |
| GET | `/api/v1/alerts/stats` | Admin | Alert statistics |
| GET | `/api/v1/analytics/dashboard` | Admin | Dashboard summary |
| GET | `/api/v1/analytics/timeline` | Admin | Time series data |
| GET | `/api/v1/analytics/risk-distribution` | Admin | Risk score distribution |
| GET | `/api/v1/analytics/false-positive-analysis` | Admin | FP cost breakdown |
| POST | `/api/v1/webhooks/razorpay` | Signature | Razorpay webhook handler |
| GET | `/api/v1/webhooks/razorpay/logs` | Admin | Webhook event logs |
| GET | `/api/v1/model/info` | None | Model metadata |
| GET | `/metrics` | None | Prometheus metrics |

## Project Structure

```
razorpay-risk-shield/
├── ml/
│   ├── scripts/
│   │   ├── train.py                # Model training pipeline
│   │   └── predict.py              # Prediction module
│   ├── models/
│   │   ├── fraud_detector_v2.joblib  # Trained model
│   │   ├── fraud_patterns.json     # 50 real fraud patterns
│   │   ├── metrics_v2.json         # Model metrics
│   │   └── feature_importances.json
│   └── data/                       # Training datasets
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI app, middleware, lifecycle
│   │   ├── core/
│   │   │   ├── config.py           # Pydantic Settings
│   │   │   ├── database.py         # Async SQLAlchemy engine
│   │   │   └── auth.py             # JWT + API key auth
│   │   ├── api/
│   │   │   ├── transactions.py     # Scoring endpoints
│   │   │   ├── orders.py           # Razorpay order creation & verification
│   │   │   ├── alerts.py           # Alert management
│   │   │   ├── analytics.py        # Dashboard & analytics
│   │   │   ├── auth.py             # Register/login/rotate key
│   │   │   └── webhooks.py         # Razorpay webhook handler
│   │   ├── models/                 # SQLAlchemy ORM models
│   │   └── services/
│   │       ├── risk_engine.py      # ML inference pipeline
│   │       ├── monitoring.py       # Prometheus metrics + drift detection
│   │       └── pci.py              # Card masking & Luhn validation
│   ├── alembic/                    # Database migrations
│   ├── tests/test_api.py           # Integration tests
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── pages/                  # Dashboard, Transactions, Alerts, Analytics
│   │   ├── components/             # RiskBadge, StatCard, Layout
│   │   └── lib/                    # API client, TypeScript types
│   ├── public/demo.html            # Razorpay checkout demo page
│   └── nginx.conf                  # SPA routing + API proxy
├── infrastructure/
│   ├── grafana-dashboard.json      # 9-panel Grafana dashboard
│   ├── grafana-provisioning/       # Auto-provisioned datasources
│   └── prometheus.yml              # Prometheus scrape config
├── scripts/
│   ├── demo_seed.py                # Quick demo setup
│   ├── demo_bulk_seed.py           # Bulk data seeding
│   └── mlflow_log_model.py         # Log model to MLflow
├── .github/workflows/ci.yml        # Lint → Test → Build pipeline
├── docker-compose.yml              # 10-service stack
├── Dockerfile.backend              # Multi-stage backend build
├── Dockerfile.frontend             # Nginx + Vite build
└── .env.example                    # Environment template
```

## Infrastructure

| Service | Purpose |
|---------|---------|
| **PostgreSQL 16** | Transaction storage, alerts, audit trail |
| **Redis 7** | Session caching, rate limiting, Celery broker |
| **Kafka** | Event streaming for real-time transaction processing |
| **Celery** | Background task processing |
| **Prometheus** | Metrics collection (predictions, latency, drift) |
| **Grafana** | Real-time monitoring dashboard (9 panels) |
| **MLflow** | ML experiment tracking and model registry |

## Security

- Card numbers are masked before storage (PCI DSS)
- JWT tokens with configurable expiry
- API key rotation support
- HMAC-SHA256 webhook signature verification
- HSTS, CORS, rate limiting headers
- Non-root Docker containers
- Secrets never committed (`.env` in `.gitignore`)
- Admin API key auto-derived when not set (dev mode)

## Built For

**Razorpay AI Buildathon 2026 — Track 2: AI Risk Manager**

"Stop the merchant losing money to fraud, returns and chargebacks."

### Defense-Only

RiskShield is strictly defense-only. It detects and prevents fraud — it does not generate, simulate, or enable fraudulent transactions.

## License

MIT

# RiskShield AI

**Track 2 — AI Risk Manager** | Razorpay AI Buildathon 2026

> Real-time payment fraud detection for merchants. Detects high-risk transactions with measured precision, recall, and false-positive cost analysis. Strictly defense-only.

## Architecture

```
┌──────────────┐     ┌──────────────┐     ┌──────────────────┐
│   Frontend   │────▶│   Backend    │────▶│   ML Model       │
│  React/Vite  │     │   FastAPI    │     │  RandomForest    │
│  Port 3000   │     │  Port 8000   │     │  Classifier      │
└──────────────┘     └──────┬───────┘     │  34 features     │
                           │              │  sklearn 1.5.2   │
                    ┌──────▼───────┐      └──────────────────┘
                    │  PostgreSQL  │
                    │  (SQLite dev)│
                    └──────┬───────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
         ┌────────┐  ┌──────────┐  ┌──────────┐
         │ Redis  │  │ Grafana  │  │ Prometheus│
         │ Cache  │  │Dashboard │  │ Metrics  │
         └────────┘  └──────────┘  └──────────┘
```

### How It Works

1. Merchant sends transaction data via REST API
2. Risk engine extracts 34 features from transaction payload
3. RandomForest model computes fraud probability (0–1)
4. Risk level assigned: low (<0.3), medium (0.3–0.6), high (0.6–0.8), critical (≥0.8)
5. High-risk transactions automatically generate alerts
6. Top-5 feature importances provided as explainability (XAI)
7. Dashboard shows real-time monitoring, alerts, and analytics

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
- Alert management (acknowledge/dismiss/resolve)
- Batch transaction scoring
- Razorpay webhook integration (payment.captured, payment.failed, disputes)
- API key + JWT authentication
- Prometheus metrics + Grafana dashboards
- Model drift detection (PSI monitoring)
- PCI DSS compliant (card numbers masked, never logged)
- PostgreSQL with async SQLAlchemy
- Docker multi-stage build with non-root user
- CI/CD pipeline (GitHub Actions)

## Quick Start

### Prerequisites
- Python 3.12+
- Node.js 20+
- PostgreSQL 16+ (or SQLite for dev)
- Docker (optional)

### Local Development

```bash
# 1. Clone and setup
git clone https://github.com/adityashirsatrao007/riskshield-ai.git
cd riskshield-ai

# 2. Backend
cd backend
pip install -r requirements.txt
cp .env.example .env  # edit with your secrets
uvicorn app.main:app --reload --port 8000

# 3. Frontend (new terminal)
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

### Docker

```bash
docker compose up --build
```

Frontend: http://localhost:3000 | Backend: http://localhost:8000

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

### Other Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/v1/auth/register` | None | Register merchant, get API key |
| POST | `/api/v1/auth/login` | API Key | Get JWT token |
| GET | `/api/v1/auth/me` | JWT | Current merchant info |
| POST | `/api/v1/transactions` | API Key | Score single transaction |
| POST | `/api/v1/transactions/batch` | API Key | Batch score transactions |
| GET | `/api/v1/alerts` | Admin | List alerts |
| PUT | `/api/v1/alerts/{id}/status` | Admin | Update alert status |
| GET | `/api/v1/alerts/stats` | Admin | Alert statistics |
| GET | `/api/v1/analytics/dashboard` | Admin | Dashboard summary |
| GET | `/api/v1/analytics/timeline` | Admin | Time series data |
| GET | `/api/v1/analytics/risk-distribution` | Admin | Risk score distribution |
| GET | `/api/v1/analytics/false-positive-analysis` | Admin | FP cost breakdown |
| POST | `/api/v1/webhooks/razorpay` | Signature | Razorpay webhook handler |
| GET | `/api/v1/model/info` | None | Model metadata |
| GET | `/metrics` | None | Prometheus metrics |

## Project Structure

```
razorpay-risk-shield/
├── ml/
│   ├── scripts/
│   │   ├── generate_data.py   # Synthetic transaction generator
│   │   ├── train.py           # Model training pipeline
│   │   └── predict.py         # Prediction module
│   ├── data/                  # Training datasets
│   └── models/                # Trained model artifacts
├── backend/
│   ├── app/
│   │   ├── main.py            # FastAPI app, middleware, lifecycle
│   │   ├── core/
│   │   │   ├── config.py      # Pydantic Settings (env validation)
│   │   │   ├── database.py    # Async SQLAlchemy engine
│   │   │   └── auth.py        # JWT + API key authentication
│   │   ├── api/
│   │   │   ├── transactions.py  # Scoring endpoints
│   │   │   ├── alerts.py        # Alert management
│   │   │   ├── analytics.py     # Dashboard & analytics
│   │   │   ├── auth.py          # Register/login/rotate key
│   │   │   └── webhooks.py      # Razorpay webhook handler
│   │   ├── models/             # SQLAlchemy ORM models
│   │   └── services/
│   │       ├── risk_engine.py   # ML inference pipeline
│   │       ├── monitoring.py    # Prometheus metrics + drift detection
│   │       └── pci.py           # Card masking & Luhn validation
│   ├── tests/test_api.py       # 13 integration tests
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── pages/              # Dashboard, Transactions, Alerts, Analytics
│   │   ├── components/         # RiskBadge, StatCard, Layout, Toast
│   │   └── lib/                # API client, TypeScript types
│   └── package.json
├── infrastructure/
│   ├── grafana-dashboard.json  # Pre-configured Grafana dashboard
│   └── prometheus.yml          # Prometheus scrape config
├── .github/workflows/ci.yml   # Lint → Test → Build pipeline
├── docker-compose.yml          # 10-service stack
├── Dockerfile                  # Multi-stage build
└── Makefile                    # Dev commands
```

## Infrastructure

- **PostgreSQL** — Transaction storage, alert management, audit trail
- **Redis** — Session caching, rate limiting
- **Prometheus** — Metrics collection (predictions, latency, drift)
- **Grafana** — Real-time monitoring dashboard (port 3001)
- **Razorpay Webhooks** — Live payment event processing

## Security

- Card numbers are masked before storage (PCI DSS)
- JWT tokens with configurable expiry
- API key rotation support
- HMAC-SHA256 webhook signature verification
- HSTS, CORS, rate limiting headers
- Non-root Docker containers
- Secrets never committed (`.env` in `.gitignore`)

## Built For

**Razorpay AI Buildathon 2026 — Track 2: AI Risk Manager**

"Stop the merchant losing money to fraud, returns and chargebacks."

### Defense-Only

RiskShield is strictly defense-only. It detects and prevents fraud — it does not generate, simulate, or enable fraudulent transactions.

## License

MIT

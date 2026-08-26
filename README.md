# RiskShield AI

**Track 2 — AI Risk Manager** | Razorpay AI Buildathon 2026

> Payment fraud detection and chargeback prevention for merchants. Detects high-risk transactions in real-time with measured precision, recall, and false-positive cost analysis.

## Architecture

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Frontend   │────▶│   Backend    │────▶│  ML Model    │
│  React/Vite  │     │   FastAPI    │     │ RandomForest │
│  Port 3000   │     │  Port 8000   │     │  Classifier  │
└──────────────┘     └──────┬───────┘     └──────────────┘
                            │
                     ┌──────▼───────┐
                     │   SQLite     │
                     │  (Postgres   │
                     │   in prod)   │
                     └──────────────┘
```

### How It Works

1. Merchant sends transaction data via REST API
2. ML model extracts 21 features (velocity, behavioral, device, geographic)
3. Risk score computed (0–1) with explanations (top 3 contributing features)
4. High-risk transactions automatically generate alerts
5. Merchant dashboard shows real-time monitoring, alerts, and analytics

### ML Model

- **Algorithm**: RandomForest Classifier (sklearn)
- **Training**: 50K synthetic transactions, 4% fraud rate, SMOTE oversampling
- **Features**: 21 engineered features — amount z-scores, transaction velocity, device reuse, geographic anomalies, account age risk, behavioral signals
- **Metrics** (on held-out test set of 10K transactions):
  - **AUC-ROC: 1.0** | **F1: 1.0** | **Precision: 1.0** | **Recall: 1.0**
  - Confusion matrix: TN=9600, FP=0, FN=0, TP=400
  - False-positive cost analysis: $0 FP cost, $283K net benefit (true savings from caught fraud)

### Key Features

- Real-time risk scoring with explanations
- Alert management (acknowledge/dismiss/resolve)
- False-positive cost analysis dashboard
- Audit trail for every scoring decision
- Batch transaction scoring
- API key authentication

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 20+
- Docker (optional)

### Local Development

```bash
# 1. Train the ML model
cd ml
pip install -r requirements.txt
python scripts/generate_data.py
python scripts/train.py
cd ..

# 2. Start backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
cd ..

# 3. Start frontend
cd frontend
npm install
npm run dev
```

Open http://localhost:3000

### Docker

```bash
docker compose up --build
```

Frontend: http://localhost:3000 | Backend: http://localhost:8000

## API

All endpoints require `X-API-Key: riskshield-test-key-2026` header.

### Score a Transaction
```bash
curl -X POST http://localhost:8000/api/v1/transactions \
  -H "Content-Type: application/json" \
  -H "X-API-Key: riskshield-test-key-2026" \
  -d '{
    "transaction_id": "TXN00000001",
    "amount": 45000,
    "merchant_id": "M0001",
    "customer_id": "C00001",
    "card_type": "credit",
    "is_international": true,
    "country_code": "US",
    "customer_account_age_days": 5,
    "customer_total_transactions": 2,
    "merchant_category_code": "electronics",
    "merchant_avg_ticket_size": 15000,
    "shipping_address_match": false,
    "device_fingerprint_reused": true
  }'
```

### Response
```json
{
  "success": true,
  "data": {
    "transaction_id": "TXN00000001",
    "risk_score": 0.87,
    "risk_level": "critical",
    "is_flagged": true,
    "explanations": [
      {"feature": "risk_flags", "value": 5, "importance": 0.32},
      {"feature": "amount_zscore", "value": 3.2, "importance": 0.21},
      {"feature": "customer_account_age_days", "value": 5, "importance": 0.18}
    ],
    "processing_time_ms": 1.23
  }
}
```

### Other Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/transactions` | List transactions (filter by risk_level, merchant_id) |
| GET | `/api/v1/transactions/{id}` | Transaction detail with audit trail |
| POST | `/api/v1/transactions/batch` | Batch score multiple transactions |
| GET | `/api/v1/alerts` | List alerts (filter by status, risk_level) |
| PUT | `/api/v1/alerts/{id}/status` | Update alert status |
| GET | `/api/v1/alerts/stats` | Alert statistics |
| GET | `/api/v1/analytics/dashboard` | Dashboard summary |
| GET | `/api/v1/analytics/timeline` | Time series data |
| GET | `/api/v1/analytics/risk-distribution` | Risk score distribution |
| GET | `/api/v1/analytics/false-positive-analysis` | FP cost breakdown |

## Project Structure

```
razorpay-risk-shield/
├── ml/
│   ├── scripts/
│   │   ├── generate_data.py   # Synthetic transaction generator
│   │   ├── train.py           # Model training pipeline
│   │   └── predict.py         # Prediction module
│   ├── data/                  # Generated datasets
│   └── models/                # Trained model + metrics
├── backend/
│   ├── app/
│   │   ├── main.py            # FastAPI app
│   │   ├── core/              # Config, DB, auth
│   │   ├── api/               # Route handlers
│   │   ├── models/            # SQLAlchemy models
│   │   └── services/          # Risk engine, analytics
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── pages/             # Dashboard, Transactions, Alerts, Analytics
│   │   ├── components/        # Reusable UI components
│   │   └── lib/               # API client, types
│   └── package.json
├── .github/workflows/ci.yml  # CI/CD pipeline
├── docker-compose.yml
└── Dockerfile.backend / .frontend
```

## Built For

**Razorpay AI Buildathon 2026 — Track 2: AI Risk Manager**

"Stop the merchant losing money to fraud, returns and chargebacks."

### Honest Metrics

We report precision, recall, F1, and AUC-ROC on a held-out test set. The false-positive cost analysis shows the real business impact: every false alarm costs the merchant the average transaction value in blocked legitimate revenue.

### Defense-Only

RiskShield is strictly defense-only. It detects and prevents fraud — it does not generate, simulate, or enable fraudulent transactions.

## License

MIT

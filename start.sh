#!/usr/bin/env bash
set -e

PROJECT="/home/aditya/Desktop/Projects/razorpay-risk-shield"
BACKEND="$PROJECT/backend"
FRONTEND="$PROJECT/frontend"
VENV="/home/aditya/venv"

# Kill any existing
pkill -f "uvicorn app.main:app.*8000" 2>/dev/null || true
pkill -f "vite.*5173" 2>/dev/null || true
sleep 1

# Cleanup
rm -f "$BACKEND/data/riskshield.db"
mkdir -p "$BACKEND/data"

# Start backend
cd "$BACKEND"
source "$VENV/bin/activate"
export RISKSHIELD_API_KEY=demo-key-123
export DATABASE_URL="sqlite+aiosqlite:////home/aditya/Desktop/Projects/razorpay-risk-shield/backend/data/riskshield.db"
export MODEL_PATH="/home/aditya/Desktop/Projects/razorpay-risk-shield/ml/models/fraud_detector.joblib"
export DEBUG=false
export PYTHONPATH="/home/aditya/Desktop/Projects/razorpay-risk-shield/backend"
uvicorn app.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
sleep 3

# Start frontend
cd "$FRONTEND"
npx vite --host 0.0.0.0 --port 5173 &
FRONTEND_PID=$!
sleep 3

# Verify
echo "========================================="
echo "  RiskShield AI is running!"
echo "  Backend:  http://localhost:8000 (PID $BACKEND_PID)"
echo "  Frontend: http://localhost:5173 (PID $FRONTEND_PID)"
echo "  API Key:  demo-key-123"
echo "========================================="
curl -s http://127.0.0.1:8000/health && echo ""
curl -s -o /dev/null -w "Frontend: HTTP %{http_code}\n" http://127.0.0.1:5173/

# Wait for both
wait

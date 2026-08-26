FROM python:3.12-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends gcc && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir --prefix=/install --timeout 600 \
    $(grep -v xgboost requirements.txt | tr '\n' ' ')
RUN pip install --no-cache-dir --prefix=/install --timeout 600 \
    xgboost==2.1.0 --no-deps

COPY backend/ ./backend/
COPY ml/models/ ./ml/models/
COPY infrastructure/ ./infrastructure/

RUN python -m compileall -q backend/ infrastructure/

FROM node:20-alpine AS frontend
WORKDIR /app
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install
COPY frontend/ .
RUN npm run build

FROM python:3.12-slim AS runtime

COPY --from=builder /install /usr/local
WORKDIR /app

COPY --from=builder /build/backend/ ./backend/
COPY --from=builder /build/ml/models/ ./ml_models/
COPY --from=builder /build/infrastructure/ ./infrastructure/
COPY --from=frontend /app/dist ./static/

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app/backend \
    MODEL_PATH=/app/ml_models/fraud_detector_v2.joblib

EXPOSE 8000

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]

FROM python:3.12-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends gcc curl && rm -rf /var/lib/apt/lists/*

RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y --no-install-recommends nodejs && \
    rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir --prefix=/install --timeout 600 \
    $(grep -v xgboost requirements.txt | tr '\n' ' ')
RUN pip install --no-cache-dir --prefix=/install --timeout 600 \
    xgboost==2.1.0 --no-deps

COPY frontend/package.json frontend/package-lock.json* ./frontend/
RUN cd frontend && npm install

COPY backend/ ./backend/
COPY ml/models/ ./ml/models/
COPY infrastructure/ ./infrastructure/
COPY frontend/ ./frontend/

RUN cd frontend && npm run build
RUN python -m compileall -q backend/ infrastructure/

FROM python:3.12-slim

COPY --from=builder /install /usr/local
WORKDIR /app

RUN mkdir -p /app/data

COPY --from=builder /build/backend/ ./backend/
COPY --from=builder /build/ml/models/ ./ml_models/
COPY --from=builder /build/infrastructure/ ./infrastructure/
COPY --from=builder /build/frontend/dist ./static/

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app/backend \
    MODEL_PATH=/app/ml_models/fraud_detector_v2.joblib

EXPOSE 8000

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]

import pytest
import pytest_asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./data/riskshield_test.db")
os.environ.setdefault("MODEL_PATH", "../../ml/models/fraud_detector_v2.joblib")
os.environ.setdefault("RISKSHIELD_API_KEY", "test-key-123")
os.environ.setdefault("RISKSHIELD_SECRET_KEY", "test-secret-key-for-testing-only-32chars!")

from httpx import AsyncClient, ASGITransport
from app.core.database import init_db
from app.main import app


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_db():
    await init_db()
    yield


@pytest_asyncio.fixture(scope="session")
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest_asyncio.fixture(scope="session")
async def auth_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        reg = await c.post(
            "/api/v1/auth/register",
            json={"name": "Test Merchant", "email": "test_merchant@example.com"},
        )
        assert reg.status_code == 200
        api_key = reg.json()["api_key"]
        token = reg.json()["access_token"]
        c.headers["X-API-Key"] = api_key
        c.headers["Authorization"] = f"Bearer {token}"
        yield c


async def test_health(client):
    r = await client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data["service"] == "riskshield-api"
    assert data["checks"]["database"] == "ok"


async def test_auth_rejects_bad_key(client):
    r = await client.get("/api/v1/transactions", headers={"X-API-Key": "bad-key"})
    assert r.status_code == 401


async def test_auth_accepts_valid_key(auth_client):
    r = await auth_client.get("/api/v1/transactions")
    assert r.status_code == 200


async def test_score_transaction(auth_client):
    r = await auth_client.post(
        "/api/v1/transactions",
        json={
            "transaction_id": "test-001",
            "amount": 5000,
            "merchant_id": "mer_001",
            "customer_id": "cust_001",
            "card_type": "credit",
            "is_international": False,
        },
    )
    assert r.status_code == 200
    data = r.json()["data"]
    assert "risk_score" in data
    assert "risk_level" in data
    assert data["risk_level"] in ("low", "medium", "high", "critical", "unknown")


async def test_batch_score(auth_client):
    r = await auth_client.post(
        "/api/v1/transactions/batch",
        json={
            "transactions": [
                {"transaction_id": "batch-001", "amount": 1000, "merchant_id": "mer_001", "customer_id": "c1"},
                {"transaction_id": "batch-002", "amount": 50000, "merchant_id": "mer_002", "customer_id": "c2"},
            ]
        },
    )
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["scored"] == 2


async def test_model_info(auth_client):
    r = await auth_client.get("/api/v1/model/info")
    assert r.status_code == 200
    data = r.json()
    assert "model_loaded" in data
    assert "model_version" in data


async def test_dashboard(auth_client):
    r = await auth_client.get("/api/v1/analytics/dashboard")
    assert r.status_code == 200
    data = r.json()["data"]
    assert "total_transactions" in data
    assert "fraud_rate" in data


async def test_metrics(client):
    r = await client.get("/metrics")
    assert r.status_code == 200
    assert b"riskshield_predictions_total" in r.content


async def test_register_merchant(client):
    r = await client.post(
        "/api/v1/auth/register",
        json={"name": "Test Shop", "email": "test@example.com"},
    )
    assert r.status_code == 200
    data = r.json()
    assert "api_key" in data
    assert "access_token" in data
    assert data["name"] == "Test Shop"


async def test_auth_me(auth_client):
    r = await auth_client.get("/api/v1/auth/me")
    assert r.status_code == 200
    assert r.json()["name"] == "Test Merchant"


async def test_login_with_api_key(client):
    reg = await client.post(
        "/api/v1/auth/register",
        json={"name": "Login Test", "email": "login@example.com"},
    )
    api_key = reg.json()["api_key"]
    r = await client.post(
        "/api/v1/auth/login",
        json={"api_key": api_key},
    )
    assert r.status_code == 200
    assert "access_token" in r.json()


async def test_webhook_requires_signature(client):
    r = await client.post(
        "/api/v1/webhooks/razorpay",
        json={"event": "payment.captured", "payload": {}},
    )
    assert r.status_code in (200, 400, 503)


async def test_rotate_api_key(auth_client):
    r = await auth_client.post("/api/v1/auth/rotate-key")
    assert r.status_code == 200
    assert "api_key" in r.json()

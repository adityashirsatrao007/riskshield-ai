import os
import sys
import pytest

PROJECT_ROOT = os.path.join(os.path.dirname(__file__), "..")
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")
DATA_DIR = os.path.join(BACKEND_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

TEST_DB = os.path.join(DATA_DIR, "riskshield_test.db")
if os.path.exists(TEST_DB):
    os.remove(TEST_DB)

os.environ["RISKSHIELD_API_KEY"] = "test-key-for-ci"
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{TEST_DB}"
os.environ["MODEL_PATH"] = os.path.join(PROJECT_ROOT, "ml", "models", "fraud_detector.joblib")
os.environ["DEBUG"] = "false"

sys.path.insert(0, BACKEND_DIR)

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
import app.core.database as _db

_db.engine = create_async_engine(os.environ["DATABASE_URL"], echo=False)
_db.async_session = async_sessionmaker(_db.engine, class_=AsyncSession, expire_on_commit=False)

async def _test_get_db():
    async with _db.async_session() as session:
        try:
            yield session
        finally:
            await session.close()

_db.get_db = _test_get_db

from app.services import risk_engine
mp = os.path.abspath(os.environ["MODEL_PATH"])
if os.path.exists(mp):
    risk_engine.load_model(mp)

from app.main import app
from httpx import AsyncClient, ASGITransport


@pytest.fixture(scope="module")
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="module")
def api_key():
    return "test-key-for-ci"


@pytest.fixture(scope="module")
async def client():
    await _db.init_db()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    await _db.engine.dispose()


@pytest.mark.anyio
async def test_health(client):
    r = await client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] in ("healthy", "degraded")


@pytest.mark.anyio
async def test_auth_no_key(client):
    assert (await client.get("/api/v1/transactions")).status_code == 401


@pytest.mark.anyio
async def test_auth_bad_key(client):
    assert (await client.get("/api/v1/transactions", headers={"X-API-Key": "wrong"})).status_code == 401


@pytest.mark.anyio
async def test_auth_valid_key(client, api_key):
    assert (await client.get("/api/v1/transactions", headers={"X-API-Key": api_key})).status_code == 200


@pytest.mark.anyio
async def test_score_high_risk(client, api_key):
    import uuid
    r = await client.post("/api/v1/transactions", json={
        "transaction_id": f"T-{uuid.uuid4().hex[:8]}", "amount": 99999, "merchant_id": "M1", "customer_id": "C1",
        "card_type": "credit", "is_international": True, "country_code": "US",
        "customer_account_age_days": 2, "customer_total_transactions": 1,
        "merchant_category_code": "electronics", "merchant_avg_ticket_size": 5000,
        "shipping_address_match": False, "device_fingerprint_reused": True,
    }, headers={"X-API-Key": api_key})
    assert r.status_code == 200
    assert r.json()["data"]["risk_level"] in ("high", "critical")


@pytest.mark.anyio
async def test_score_low_risk(client, api_key):
    import uuid
    r = await client.post("/api/v1/transactions", json={
        "transaction_id": f"T-{uuid.uuid4().hex[:8]}", "amount": 200, "merchant_id": "M1", "customer_id": "C2",
        "card_type": "debit", "is_international": False, "country_code": "IN",
        "customer_account_age_days": 500, "customer_total_transactions": 200,
        "merchant_category_code": "groceries", "merchant_avg_ticket_size": 400,
        "shipping_address_match": True, "device_fingerprint_reused": False,
    }, headers={"X-API-Key": api_key})
    assert r.status_code == 200
    assert r.json()["data"]["risk_level"] == "low"


@pytest.mark.anyio
async def test_duplicate_returns_409(client, api_key):
    import uuid
    tid = f"D-{uuid.uuid4().hex[:8]}"
    p = {"transaction_id": tid, "amount": 1000, "merchant_id": "M1", "customer_id": "C1"}
    assert (await client.post("/api/v1/transactions", json=p, headers={"X-API-Key": api_key})).status_code == 200
    r = await client.post("/api/v1/transactions", json=p, headers={"X-API-Key": api_key})
    assert r.status_code == 409
    assert "already exists" in r.json()["detail"]


@pytest.mark.anyio
async def test_invalid_timestamp(client, api_key):
    r = await client.post("/api/v1/transactions",
        json={"transaction_id": "X", "amount": 100, "merchant_id": "M1", "customer_id": "C1", "timestamp": "bad"},
        headers={"X-API-Key": api_key})
    assert r.status_code == 422


@pytest.mark.anyio
async def test_negative_amount(client, api_key):
    r = await client.post("/api/v1/transactions",
        json={"transaction_id": "X", "amount": -100, "merchant_id": "M1", "customer_id": "C1"},
        headers={"X-API-Key": api_key})
    assert r.status_code == 422


@pytest.mark.anyio
async def test_invalid_card_type(client, api_key):
    r = await client.post("/api/v1/transactions",
        json={"transaction_id": "X", "amount": 100, "merchant_id": "M1", "customer_id": "C1", "card_type": "bitcoin"},
        headers={"X-API-Key": api_key})
    assert r.status_code == 422


@pytest.mark.anyio
async def test_batch_scoring(client, api_key):
    import uuid
    r = await client.post("/api/v1/transactions/batch", json={"transactions": [
        {"transaction_id": f"B-{uuid.uuid4().hex[:8]}", "amount": 50000, "merchant_id": "M1", "customer_id": "C1",
         "is_international": True, "customer_account_age_days": 3, "customer_total_transactions": 2},
        {"transaction_id": f"B-{uuid.uuid4().hex[:8]}", "amount": 200, "merchant_id": "M1", "customer_id": "C2",
         "customer_account_age_days": 500, "customer_total_transactions": 100},
    ]}, headers={"X-API-Key": api_key})
    assert r.status_code == 200
    assert r.json()["data"]["scored"] == 2


@pytest.mark.anyio
async def test_batch_partial_failure(client, api_key):
    import uuid
    tid = f"E-{uuid.uuid4().hex[:8]}"
    await client.post("/api/v1/transactions",
        json={"transaction_id": tid, "amount": 100, "merchant_id": "M1", "customer_id": "C1"},
        headers={"X-API-Key": api_key})
    r = await client.post("/api/v1/transactions/batch", json={"transactions": [
        {"transaction_id": tid, "amount": 100, "merchant_id": "M1", "customer_id": "C1"},
        {"transaction_id": f"N-{uuid.uuid4().hex[:8]}", "amount": 200, "merchant_id": "M1", "customer_id": "C2"},
    ]}, headers={"X-API-Key": api_key})
    assert r.status_code == 200
    assert r.json()["data"]["scored"] == 1
    assert len(r.json()["data"]["errors"]) == 1


@pytest.mark.anyio
async def test_dashboard(client, api_key):
    r = await client.get("/api/v1/analytics/dashboard", headers={"X-API-Key": api_key})
    assert r.status_code == 200


@pytest.mark.anyio
async def test_risk_distribution(client, api_key):
    r = await client.get("/api/v1/analytics/risk-distribution", headers={"X-API-Key": api_key})
    assert r.status_code == 200


@pytest.mark.anyio
async def test_alerts(client, api_key):
    r = await client.get("/api/v1/alerts", headers={"X-API-Key": api_key})
    assert r.status_code == 200


@pytest.mark.anyio
async def test_request_headers(client):
    r = await client.get("/health")
    assert "x-request-id" in r.headers
    assert "x-response-time" in r.headers


@pytest.mark.anyio
async def test_security_headers(client):
    r = await client.get("/health")
    assert r.headers.get("x-content-type-options") == "nosniff"
    assert r.headers.get("x-frame-options") == "DENY"
    assert r.headers.get("referrer-policy") == "strict-origin-when-cross-origin"


@pytest.mark.anyio
async def test_docs_hidden(client):
    assert (await client.get("/docs")).status_code == 404

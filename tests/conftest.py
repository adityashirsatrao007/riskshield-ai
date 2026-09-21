import asyncio
import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

os.environ.setdefault("RISKSHIELD_API_KEY", "test-key-for-ci")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./data/riskshield_test.db")
os.environ.setdefault("MODEL_PATH", "../ml/models/fraud_detector.joblib")
os.environ.setdefault("DEBUG", "false")


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def api_key():
    return os.environ["RISKSHIELD_API_KEY"]

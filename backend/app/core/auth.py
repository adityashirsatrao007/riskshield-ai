import os
import hmac
from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader

API_KEY = os.environ.get("RISKSHIELD_API_KEY", "riskshield-test-key-2026")
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(api_key: str = Security(api_key_header)):
    if api_key is None or not hmac.compare_digest(api_key, API_KEY):
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    return api_key

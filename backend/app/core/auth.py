import os
import sys
import hmac
import secrets
from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader

_api_key = os.environ.get("RISKSHIELD_API_KEY")
if not _api_key:
    print(
        "FATAL: RISKSHIELD_API_KEY environment variable is not set. "
        "Generate one with: python -c \"import secrets; print(secrets.token_urlsafe(32))\"",
        file=sys.stderr,
    )
    sys.exit(1)

API_KEY = _api_key
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(api_key: str = Security(api_key_header)):
    if api_key is None or not hmac.compare_digest(api_key, API_KEY):
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    return api_key

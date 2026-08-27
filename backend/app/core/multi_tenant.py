import logging
import secrets
import time
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException

logger = logging.getLogger("riskshield")

_merchants: dict[str, dict[str, Any]] = {}
_rate_limits: dict[str, list[float]] = {}


def generate_api_key() -> str:
    return secrets.token_urlsafe(32)


class MerchantManager:
    @staticmethod
    def create_merchant(
        name: str,
        rate_limit: int = 120,
        status: str = "active",
    ) -> dict[str, Any]:
        merchant_id = secrets.token_urlsafe(8)
        api_key = generate_api_key()
        now = datetime.now(timezone.utc).isoformat()

        merchant = {
            "id": merchant_id,
            "name": name,
            "api_key": api_key,
            "rate_limit": rate_limit,
            "status": status,
            "created_at": now,
            "updated_at": now,
        }
        _merchants[merchant_id] = merchant
        logger.info("Merchant created: %s (%s)", name, merchant_id)
        return merchant

    @staticmethod
    def get_merchant(merchant_id: str) -> dict[str, Any] | None:
        return _merchants.get(merchant_id)

    @staticmethod
    def get_merchant_by_api_key(api_key: str) -> dict[str, Any] | None:
        for merchant in _merchants.values():
            if merchant["api_key"] == api_key:
                return merchant
        return None

    @staticmethod
    def list_merchants(status: str | None = None) -> list[dict[str, Any]]:
        merchants = list(_merchants.values())
        if status:
            merchants = [m for m in merchants if m["status"] == status]
        return merchants

    @staticmethod
    def update_merchant(merchant_id: str, **kwargs: Any) -> dict[str, Any] | None:
        merchant = _merchants.get(merchant_id)
        if not merchant:
            return None
        for key, value in kwargs.items():
            if key in ("name", "rate_limit", "status"):
                merchant[key] = value
        merchant["updated_at"] = datetime.now(timezone.utc).isoformat()
        return merchant

    @staticmethod
    def delete_merchant(merchant_id: str) -> bool:
        if merchant_id in _merchants:
            del _merchants[merchant_id]
            _rate_limits.pop(merchant_id, None)
            logger.info("Merchant deleted: %s", merchant_id)
            return True
        return False

    @staticmethod
    def get_active_count() -> int:
        return sum(1 for m in _merchants.values() if m["status"] == "active")


def _check_rate_limit(merchant_id: str, rate_limit: int) -> bool:
    now = time.time()
    window = 60.0

    if merchant_id not in _rate_limits:
        _rate_limits[merchant_id] = []

    _rate_limits[merchant_id] = [
        t for t in _rate_limits[merchant_id] if now - t < window
    ]

    if len(_rate_limits[merchant_id]) >= rate_limit:
        return False

    _rate_limits[merchant_id].append(now)
    return True


def _cleanup_stale_limits() -> None:
    now = time.time()
    stale = [k for k, v in _rate_limits.items() if not v or v[-1] < now - 60]
    for k in stale:
        del _rate_limits[k]


class MerchantMiddleware:
    def __init__(self, app: Any) -> None:
        self.app = app

    async def __call__(self, scope: dict, receive: Any, send: Any) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        from starlette.requests import Request

        request = Request(scope, receive)

        skip_paths = ("/health", "/metrics", "/docs", "/redoc", "/openapi.json")
        if request.url.path in skip_paths:
            await self.app(scope, receive, send)
            return

        api_key = request.headers.get("X-API-Key")
        if not api_key:
            response = HTTPException(status_code=401, detail="Missing X-API-Key header")

            await send(
                {
                    "type": "http.response.start",
                    "status": response.status_code,
                    "headers": [[b"content-type", b"application/json"]],
                }
            )
            await send(
                {
                    "type": "http.response.body",
                    "body": b'{"detail":"Missing X-API-Key header"}',
                }
            )
            return

        merchant = MerchantManager.get_merchant_by_api_key(api_key)
        if not merchant:

            await send(
                {
                    "type": "http.response.start",
                    "status": 401,
                    "headers": [[b"content-type", b"application/json"]],
                }
            )
            await send(
                {
                    "type": "http.response.body",
                    "body": b'{"detail":"Invalid API key"}',
                }
            )
            return

        if merchant["status"] != "active":

            await send(
                {
                    "type": "http.response.start",
                    "status": 403,
                    "headers": [[b"content-type", b"application/json"]],
                }
            )
            await send(
                {
                    "type": "http.response.body",
                    "body": b'{"detail":"Merchant account suspended"}',
                }
            )
            return

        if not _check_rate_limit(merchant["id"], merchant["rate_limit"]):

            await send(
                {
                    "type": "http.response.start",
                    "status": 429,
                    "headers": [
                        [b"content-type", b"application/json"],
                        [b"retry-after", b"60"],
                    ],
                }
            )
            await send(
                {
                    "type": "http.response.body",
                    "body": b'{"detail":"Rate limit exceeded for merchant"}',
                }
            )
            return

        scope["merchant_id"] = merchant["id"]
        scope["merchant_name"] = merchant["name"]
        scope["merchant_rate_limit"] = merchant["rate_limit"]

        await self.app(scope, receive, send)

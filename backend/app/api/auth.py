from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from ..core.config import settings


class APIKeyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path.startswith("/health") or request.url.path == "/":
            return await call_next(request)

        api_key = request.headers.get("X-API-Key")
        if api_key != settings.API_KEY:
            return JSONResponse(
                status_code=401,
                content={"success": False, "error": "Invalid or missing X-API-Key header"},
            )
        return await call_next(request)

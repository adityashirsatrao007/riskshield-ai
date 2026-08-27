import logging
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException, Request

logger = logging.getLogger("riskshield")
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer(auto_error=False)


def hash_api_key(api_key: str) -> str:
    return pwd_context.hash(api_key)


def verify_api_key_plain(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.JWT_EXPIRY_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


async def get_current_merchant(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: AsyncSession = Depends(get_db),
):
    from app.models.merchant import Merchant

    if credentials and credentials.credentials:
        payload = decode_token(credentials.credentials)
        merchant_id = payload.get("sub")
        if not merchant_id:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        result = await db.execute(select(Merchant).where(Merchant.id == int(merchant_id)))
        merchant = result.scalar_one_or_none()
        if not merchant or not merchant.is_active:
            raise HTTPException(status_code=401, detail="Merchant not found or inactive")
        return merchant

    raise HTTPException(status_code=401, detail="Authentication required")


async def verify_api_key(request: Request, db: AsyncSession = Depends(get_db)):
    api_key = request.headers.get("X-API-Key")
    if not api_key:
        raise HTTPException(status_code=401, detail="Missing X-API-Key header")

    from app.models.merchant import Merchant

    result = await db.execute(
        select(Merchant.api_key_hash).where(Merchant.is_active == True)
    )
    hashes = [row[0] for row in result.all()]

    for h in hashes:
        if verify_api_key_plain(api_key, h):
            return api_key

    if api_key == settings.RISKSHIELD_API_KEY:
        logger.warning("Admin API key used for auth (not a registered merchant)")
        return api_key

    raise HTTPException(status_code=401, detail="Invalid API key")


async def require_admin(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    api_key = request.headers.get("X-API-Key")
    if not api_key:
        raise HTTPException(status_code=401, detail="Missing X-API-Key header")

    from app.models.merchant import Merchant

    result = await db.execute(
        select(Merchant).where(Merchant.is_active == True)
    )
    merchants = result.scalars().all()

    for m in merchants:
        if verify_api_key_plain(api_key, m.api_key_hash):
            return m

    if api_key == settings.RISKSHIELD_API_KEY:
        logger.warning("Admin API key used for merchant lookup")
        return None

    raise HTTPException(status_code=401, detail="Invalid API key")

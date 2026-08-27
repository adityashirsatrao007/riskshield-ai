from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
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


async def verify_api_key(request: Request, db: AsyncSession = Depends(get_db)):
    api_key = request.headers.get("X-API-Key")
    if not api_key:
        raise HTTPException(status_code=401, detail="Missing X-API-Key header")

    from app.models.merchant import Merchant
    result = await db.execute(select(Merchant).where(Merchant.is_active == True))
    merchants = result.scalars().all()

    for merchant in merchants:
        if verify_api_key_plain(api_key, merchant.api_key_hash):
            return merchant.api_key

    if api_key == settings.RISKSHIELD_API_KEY:
        return api_key

    raise HTTPException(status_code=401, detail="Invalid API key")


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.JWT_EXPIRY_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


async def get_current_merchant(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    x_api_key: Optional[str] = None,
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


async def require_api_key(request: Request, db: AsyncSession = Depends(get_db)):
    api_key = request.headers.get("X-API-Key")
    if not api_key:
        raise HTTPException(status_code=401, detail="Missing X-API-Key header")

    from app.models.merchant import Merchant

    result = await db.execute(select(Merchant))
    merchants = result.scalars().all()

    for merchant in merchants:
        if verify_api_key(api_key, merchant.api_key_hash):
            if not merchant.is_active:
                raise HTTPException(status_code=403, detail="Merchant account suspended")
            return merchant

    if api_key == settings.RISKSHIELD_API_KEY:
        return None

    raise HTTPException(status_code=401, detail="Invalid API key")

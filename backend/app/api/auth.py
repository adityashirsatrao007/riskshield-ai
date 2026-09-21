import secrets

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import create_access_token, get_current_merchant, hash_api_key, verify_api_key_plain
from app.core.database import get_db
from app.models.merchant import Merchant

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    tier: str = "free"


class RegisterResponse(BaseModel):
    merchant_id: int
    name: str
    api_key: str
    access_token: str
    tier: str


class LoginRequest(BaseModel):
    api_key: str


class LoginResponse(BaseModel):
    access_token: str
    merchant_id: int
    name: str
    tier: str


@router.post("/register", response_model=RegisterResponse)
async def register_merchant(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(Merchant).where(Merchant.email == body.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Email already registered")

    raw_key = f"rsk_{secrets.token_urlsafe(32)}"
    hashed = hash_api_key(raw_key)

    merchant = Merchant(
        name=body.name,
        email=body.email,
        api_key_hash=hashed,
        tier=body.tier,
    )
    db.add(merchant)
    await db.commit()
    await db.refresh(merchant)

    token = create_access_token({"sub": str(merchant.id), "tier": merchant.tier})

    return RegisterResponse(
        merchant_id=merchant.id,
        name=merchant.name,
        api_key=raw_key,
        access_token=token,
        tier=merchant.tier,
    )


@router.post("/login", response_model=LoginResponse)
async def login_merchant(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Merchant).where(Merchant.is_active == True))
    merchants = result.scalars().all()

    for merchant in merchants:
        if verify_api_key_plain(body.api_key, merchant.api_key_hash):
            token = create_access_token({"sub": str(merchant.id), "tier": merchant.tier})
            return LoginResponse(
                access_token=token,
                merchant_id=merchant.id,
                name=merchant.name,
                tier=merchant.tier,
            )

    raise HTTPException(status_code=401, detail="Invalid API key")


@router.get("/me")
async def get_me(merchant: Merchant = Depends(get_current_merchant)):
    return {
        "id": merchant.id,
        "name": merchant.name,
        "email": merchant.email,
        "tier": merchant.tier,
        "is_active": merchant.is_active,
        "created_at": merchant.created_at.isoformat() if merchant.created_at else None,
    }


@router.post("/rotate-key")
async def rotate_api_key(
    merchant: Merchant = Depends(get_current_merchant),
    db: AsyncSession = Depends(get_db),
):
    new_raw = f"rsk_{secrets.token_urlsafe(32)}"
    merchant.api_key_hash = hash_api_key(new_raw)
    await db.commit()
    return {"api_key": new_raw, "message": "Key rotated. Update your integrations."}

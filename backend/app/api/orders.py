import logging
import time
from typing import Optional

import razorpay
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.core.auth import require_admin
from app.core.config import settings

logger = logging.getLogger("riskshield.orders")

router = APIRouter(prefix="/orders", tags=["orders"])


def _get_razorpay_client() -> razorpay.Client | None:
    if not settings.RAZORPAY_KEY_ID or not settings.RAZORPAY_KEY_SECRET:
        return None
    return razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))


class OrderCreateRequest(BaseModel):
    amount: float = Field(..., gt=0, le=1_000_000, description="Amount in INR")
    currency: str = Field(default="INR", min_length=3, max_length=3)
    receipt: Optional[str] = Field(default=None, max_length=40)
    notes: Optional[dict] = Field(default=None)


class OrderResponse(BaseModel):
    order_id: str
    amount: int
    currency: str
    key_id: str
    receipt: Optional[str]


class PaymentVerifyRequest(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str


@router.post("", response_model=OrderResponse)
async def create_order(
    req: OrderCreateRequest,
    _auth=Depends(require_admin),
):
    client = _get_razorpay_client()
    if not client:
        raise HTTPException(
            status_code=503,
            detail="Razorpay not configured. Set RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET.",
        )

    amount_paise = int(req.amount * 100)
    receipt = req.receipt or f"rs_{int(time.time())}"

    try:
        order = client.order.create({
            "amount": amount_paise,
            "currency": req.currency,
            "receipt": receipt,
            "notes": req.notes or {},
        })
    except razorpay.errors.BadRequestError as e:
        logger.error("Razorpay order creation failed: %s", e)
        raise HTTPException(status_code=400, detail=f"Razorpay error: {str(e)}")
    except Exception as e:
        logger.error("Razorpay order creation error: %s", e)
        raise HTTPException(status_code=502, detail="Failed to create order")

    logger.info("Order created: id=%s amount=%d currency=%s", order["id"], amount_paise, req.currency)

    return OrderResponse(
        order_id=order["id"],
        amount=amount_paise,
        currency=req.currency,
        key_id=settings.RAZORPAY_KEY_ID,
        receipt=receipt,
    )


@router.post("/verify")
async def verify_payment(
    req: PaymentVerifyRequest,
    _auth=Depends(require_admin),
):
    import hashlib
    import hmac as _hmac

    if not settings.RAZORPAY_KEY_SECRET:
        raise HTTPException(status_code=503, detail="Razorpay not configured")

    body = f"{req.razorpay_order_id}|{req.razorpay_payment_id}"
    expected = _hmac.new(
        settings.RAZORPAY_KEY_SECRET.encode(), body.encode(), hashlib.sha256
    ).hexdigest()

    if not _hmac.compare_digest(expected, req.razorpay_signature):
        logger.warning("Payment verification failed: order=%s", req.razorpay_order_id)
        raise HTTPException(status_code=400, detail="Invalid payment signature")

    logger.info("Payment verified: order=%s payment=%s", req.razorpay_order_id, req.razorpay_payment_id)

    return {"status": "verified", "order_id": req.razorpay_order_id, "payment_id": req.razorpay_payment_id}

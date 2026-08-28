import hashlib
import hmac
import json
import logging
from typing import Optional
from fastapi import APIRouter, Request, HTTPException, Header
from pydantic import BaseModel

logger = logging.getLogger("riskshield.webhooks")
router = APIRouter(prefix="/webhooks", tags=["webhooks"])


class WebhookLog(BaseModel):
    event_type: str
    payload_hash: str
    status: str
    processed_at: str


_webhook_log: list[WebhookLog] = []


def verify_razorpay_signature(
    body: bytes, signature: str, secret: str
) -> bool:
    if not signature or not secret:
        return False
    expected = hmac.new(
        secret.encode(), body, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


@router.post("/razorpay")
async def handle_razorpay_webhook(
    request: Request,
    x_razorpay_signature: Optional[str] = Header(None),
):
    from datetime import datetime, timezone
    from app.core.config import settings

    body = await request.body()

    if not settings.RAZORPAY_WEBHOOK_SECRET:
        logger.error("Webhook received but RAZORPAY_WEBHOOK_SECRET not configured")
        raise HTTPException(
            status_code=503,
            detail="Webhook processing not configured. Set RAZORPAY_WEBHOOK_SECRET.",
        )

    if not x_razorpay_signature:
        logger.warning("Missing Razorpay signature header")
        raise HTTPException(status_code=400, detail="Missing webhook signature")

    if not verify_razorpay_signature(body, x_razorpay_signature, settings.RAZORPAY_WEBHOOK_SECRET):
        logger.warning("Invalid Razorpay webhook signature")
        raise HTTPException(status_code=400, detail="Invalid webhook signature")

    try:
        event = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    event_type = event.get("event", "unknown")
    payload_hash = hashlib.sha256(body).hexdigest()[:16]

    logger.info("Webhook received: %s (hash: %s)", event_type, payload_hash)

    if event_type == "payment.captured":
        await _handle_payment_captured(event.get("payload", {}))
    elif event_type == "payment.failed":
        await _handle_payment_failed(event.get("payload", {}))
    elif event_type == "payment.authorized":
        await _handle_payment_authorized(event.get("payload", {}))
    elif event_type.startswith("dispute."):
        await _handle_dispute(event_type, event.get("payload", {}))
    elif event_type == "order.paid":
        await _handle_order_paid(event.get("payload", {}))
    else:
        logger.info("Unhandled event type: %s", event_type)

    log_entry = WebhookLog(
        event_type=event_type,
        payload_hash=payload_hash,
        status="processed",
        processed_at=datetime.now(timezone.utc).isoformat(),
    )
    _webhook_log.append(log_entry)
    if len(_webhook_log) > 1000:
        _webhook_log.pop(0)

    return {"status": "ok", "event_type": event_type}


async def _handle_payment_captured(payload: dict):
    from datetime import datetime, timezone
    from app.services import risk_engine
    from app.core.database import async_session
    from app.models.transaction import Transaction, Alert, AuditTrail

    payment = payload.get("payment", {}).get("entity", {})
    amount = payment.get("amount", 0) / 100
    order_id = payment.get("order_id", "")
    payment_id = payment.get("id", "")

    logger.info(
        "Payment captured: id=%s order=%s amount=%.2f — scoring transaction",
        payment_id, order_id, amount,
    )

    merchant_id = payment.get("notes", {}).get("merchant_id", "demo_merchant")
    customer_id = payment.get("notes", {}).get("customer_id", "demo_customer")

    txn_data = {
        "transaction_id": payment_id or order_id,
        "amount": amount,
        "currency": payment.get("currency", "INR"),
        "merchant_id": merchant_id,
        "customer_id": customer_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    if risk_engine.is_loaded():
        result = risk_engine.score_transaction(txn_data)
        logger.info(
            "Auto-scored payment %s: risk=%.4f level=%s flagged=%s",
            payment_id, result["risk_score"], result["risk_level"], result["is_flagged"],
        )

        try:
            async with async_session() as db:
                db_txn = Transaction(
                    transaction_id=payment_id or order_id,
                    amount=amount,
                    currency=payment.get("currency", "INR"),
                    merchant_id=merchant_id,
                    customer_id=customer_id,
                    timestamp=datetime.now(timezone.utc),
                    card_type="card",
                    risk_score=result["risk_score"],
                    risk_level=result["risk_level"],
                    is_flagged=result["is_flagged"],
                )
                db.add(db_txn)
                await db.flush()

                audit = AuditTrail(
                    transaction_id=db_txn.id,
                    action="webhook_score",
                    details={
                        "payment_id": payment_id,
                        "order_id": order_id,
                        "source": "razorpay_webhook",
                        "explanations": result["explanations"],
                    },
                    model_version=result["model_version"],
                    processing_time_ms=result["processing_time_ms"],
                )
                db.add(audit)

                if result["is_flagged"]:
                    alert = Alert(
                        transaction_id=db_txn.id,
                        risk_score=result["risk_score"],
                        risk_level=result["risk_level"],
                        explanation=result["explanations"],
                        status="open",
                    )
                    db.add(alert)

                await db.commit()
                logger.info("Payment %s persisted to DB (risk=%.4f)", payment_id, result["risk_score"])
        except Exception as e:
            logger.error("Failed to persist webhook payment: %s", e)

        from app.services.monitoring import PREDICTIONS_TOTAL, FRAUD_DETECTED_TOTAL, PROCESSING_TIME
        PREDICTIONS_TOTAL.labels(merchant_id=merchant_id, risk_level=result["risk_level"]).inc()
        if result["is_flagged"]:
            FRAUD_DETECTED_TOTAL.labels(merchant_id=merchant_id).inc()
        PROCESSING_TIME.observe(result["processing_time_ms"] / 1000.0)


async def _handle_payment_failed(payload: dict):
    payment = payload.get("payment", {}).get("entity", {})
    error_code = payment.get("error_code", "unknown")
    logger.warning(
        "Payment failed: id=%s error=%s",
        payment.get("id", ""), error_code,
    )


async def _handle_payment_authorized(payload: dict):
    payment = payload.get("payment", {}).get("entity", {})
    logger.info("Payment authorized: id=%s", payment.get("id", ""))


async def _handle_dispute(event_type: str, payload: dict):
    dispute = payload.get("dispute", {}).get("entity", {})
    logger.warning(
        "Dispute event: %s dispute_id=%s amount=%s",
        event_type, dispute.get("id", ""), dispute.get("amount", 0),
    )


async def _handle_order_paid(payload: dict):
    order = payload.get("order", {}).get("entity", {})
    logger.info("Order paid: id=%s amount=%s", order.get("id", ""), order.get("amount", 0))


@router.get("/razorpay/logs")
async def get_webhook_logs():
    from app.core.auth import verify_api_key
    from fastapi import Depends
    return {"success": True, "data": [log.model_dump() for log in _webhook_log[-50:]]}

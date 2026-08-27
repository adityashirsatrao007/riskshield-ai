import asyncio
import logging
from datetime import datetime, timezone
from functools import partial

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import BatchTransaction, TransactionCreate
from app.core.auth import verify_api_key
from app.core.database import get_db
from app.models.transaction import Alert, AuditTrail, Transaction
from app.services import risk_engine
from app.services.pci import mask_card_number, mask_sensitive_fields, validate_card_format

logger = logging.getLogger("riskshield")

router = APIRouter(prefix="/transactions", tags=["transactions"])


def _get_prediction_logger():
    from app.main import prediction_logger
    return prediction_logger


def _get_metrics_collector():
    from app.main import metrics_collector
    return metrics_collector


def _run_scoring_sync(txn: TransactionCreate, ts: datetime, merchant_id: str) -> dict:
    txn_dict = txn.model_dump()
    txn_dict["hour_of_day"] = ts.hour
    txn_dict["day_of_week"] = ts.weekday()
    txn_dict["timestamp"] = ts.isoformat()

    if txn.card_number:
        if validate_card_format(txn.card_number):
            txn_dict["card_masked"] = mask_card_number(txn.card_number)
        else:
            txn_dict["card_masked"] = "****"

    txn_dict.pop("card_number", None)

    result = risk_engine.score_transaction(txn_dict)

    try:
        logger_inst = _get_prediction_logger()
        logger_inst.log(
            transaction_id=txn.transaction_id,
            merchant_id=merchant_id,
            risk_score=result["risk_score"],
            risk_level=result["risk_level"],
            is_flagged=result["is_flagged"],
            processing_time_ms=result["processing_time_ms"],
            features_used=result.get("features_used", []),
        )
        metrics = _get_metrics_collector()
        metrics._predictions_counter.inc()
        if result["is_flagged"]:
            metrics._flagged_counter.inc()
        metrics._prediction_latency.observe(result["processing_time_ms"] / 1000.0)
    except Exception as e:
        logger.warning("Failed to log prediction metrics: %s", e)

    return result


async def _run_scoring(txn: TransactionCreate, ts: datetime, merchant_id: str) -> dict:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None, partial(_run_scoring_sync, txn, ts, merchant_id)
    )


@router.post("")
async def create_transaction(
    txn: TransactionCreate,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    ts = datetime.fromisoformat(txn.timestamp) if txn.timestamp else datetime.now(timezone.utc)

    result = await _run_scoring(txn, ts, txn.merchant_id)

    masked_txn = mask_sensitive_fields(txn.model_dump())

    db_txn = Transaction(
        transaction_id=txn.transaction_id,
        amount=txn.amount,
        currency=txn.currency,
        merchant_id=txn.merchant_id,
        customer_id=txn.customer_id,
        timestamp=ts,
        card_type=txn.card_type,
        is_international=txn.is_international,
        risk_score=result["risk_score"],
        risk_level=result["risk_level"],
        is_flagged=result["is_flagged"],
    )
    db.add(db_txn)

    try:
        await db.flush()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=409,
            detail=f"Transaction with id '{txn.transaction_id}' already exists",
        )

    audit = AuditTrail(
        transaction_id=db_txn.id,
        action="score",
        details={
            "features": masked_txn,
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
    await db.refresh(db_txn)

    return {
        "success": True,
        "data": {
            "transaction_id": db_txn.transaction_id,
            "risk_score": result["risk_score"],
            "risk_level": result["risk_level"],
            "is_flagged": result["is_flagged"],
            "explanations": result["explanations"],
            "processing_time_ms": result["processing_time_ms"],
        },
    }


@router.post("/batch")
async def batch_score(
    batch: BatchTransaction,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    results = []
    errors = []

    for i, txn in enumerate(batch.transactions):
        ts = datetime.fromisoformat(txn.timestamp) if txn.timestamp else datetime.now(timezone.utc)

        result = await _run_scoring(txn, ts, txn.merchant_id)

        db_txn = Transaction(
            transaction_id=txn.transaction_id,
            amount=txn.amount,
            currency=txn.currency,
            merchant_id=txn.merchant_id,
            customer_id=txn.customer_id,
            timestamp=ts,
            card_type=txn.card_type,
            is_international=txn.is_international,
            risk_score=result["risk_score"],
            risk_level=result["risk_level"],
            is_flagged=result["is_flagged"],
        )
        db.add(db_txn)

        try:
            await db.flush()
        except IntegrityError:
            await db.rollback()
            errors.append({
                "index": i,
                "transaction_id": txn.transaction_id,
                "error": "duplicate transaction_id",
            })
            continue

        if result["is_flagged"]:
            alert = Alert(
                transaction_id=db_txn.id,
                risk_score=result["risk_score"],
                risk_level=result["risk_level"],
                explanation=result["explanations"],
                status="open",
            )
            db.add(alert)

        results.append({
            "transaction_id": txn.transaction_id,
            "risk_score": result["risk_score"],
            "risk_level": result["risk_level"],
            "is_flagged": result["is_flagged"],
        })

    await db.commit()
    return {
        "success": True,
        "data": {
            "scored": len(results),
            "errors": errors,
            "results": results,
        },
    }


@router.get("")
async def list_transactions(
    risk_level: str | None = None,
    merchant_id: str | None = None,
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    query = select(Transaction)
    count_query = select(func.count(Transaction.id))

    if risk_level:
        query = query.where(Transaction.risk_level == risk_level)
        count_query = count_query.where(Transaction.risk_level == risk_level)
    if merchant_id:
        query = query.where(Transaction.merchant_id == merchant_id)
        count_query = count_query.where(Transaction.merchant_id == merchant_id)

    total = (await db.execute(count_query)).scalar()
    result = await db.execute(
        query.order_by(desc(Transaction.created_at)).offset(offset).limit(limit)
    )
    txns = result.scalars().all()

    return {
        "success": True,
        "data": [
            {
                "id": t.id,
                "transaction_id": t.transaction_id,
                "amount": float(t.amount) if t.amount else 0.0,
                "currency": t.currency,
                "merchant_id": t.merchant_id,
                "customer_id": t.customer_id,
                "timestamp": t.timestamp.isoformat(),
                "card_type": t.card_type,
                "is_international": t.is_international,
                "risk_score": t.risk_score,
                "risk_level": t.risk_level,
                "is_flagged": t.is_flagged,
                "is_resolved": t.is_resolved,
                "created_at": t.created_at.isoformat(),
            }
            for t in txns
        ],
        "total": total,
        "offset": offset,
        "limit": limit,
    }


@router.get("/{txn_id}")
async def get_transaction(
    txn_id: int,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    result = await db.execute(select(Transaction).where(Transaction.id == txn_id))
    txn = result.scalar_one_or_none()
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")

    audit_result = await db.execute(
        select(AuditTrail).where(AuditTrail.transaction_id == txn_id)
    )
    audits = audit_result.scalars().all()

    return {
        "success": True,
        "data": {
            "id": txn.id,
            "transaction_id": txn.transaction_id,
            "amount": float(txn.amount) if txn.amount else 0.0,
            "currency": txn.currency,
            "merchant_id": txn.merchant_id,
            "customer_id": txn.customer_id,
            "timestamp": txn.timestamp.isoformat(),
            "card_type": txn.card_type,
            "is_international": txn.is_international,
            "risk_score": txn.risk_score,
            "risk_level": txn.risk_level,
            "is_flagged": txn.is_flagged,
            "is_resolved": txn.is_resolved,
            "created_at": txn.created_at.isoformat(),
            "audit_trail": [
                {
                    "action": a.action,
                    "model_version": a.model_version,
                    "processing_time_ms": a.processing_time_ms,
                    "details": mask_sensitive_fields(a.details) if isinstance(a.details, dict) else a.details,
                    "created_at": a.created_at.isoformat(),
                }
                for a in audits
            ],
        },
    }

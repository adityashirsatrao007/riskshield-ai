from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, desc
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.auth import verify_api_key
from app.models.transaction import Transaction, Alert, AuditTrail
from app.services.risk_engine import score_transaction
from app.api.schemas import TransactionCreate, BatchTransaction

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.post("")
async def create_transaction(
    txn: TransactionCreate,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    ts = datetime.fromisoformat(txn.timestamp) if txn.timestamp else datetime.now(timezone.utc)
    hour = ts.hour
    day = ts.weekday()

    txn_dict = txn.model_dump()
    txn_dict["hour_of_day"] = hour
    txn_dict["day_of_week"] = day
    txn_dict["timestamp"] = ts.isoformat()

    result = score_transaction(txn_dict)

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
            "features": txn_dict,
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
        txn_dict = txn.model_dump()
        txn_dict["hour_of_day"] = ts.hour
        txn_dict["day_of_week"] = ts.weekday()
        txn_dict["timestamp"] = ts.isoformat()

        result = score_transaction(txn_dict)

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
    risk_level: str = None,
    merchant_id: str = None,
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
                "amount": t.amount,
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
            "amount": txn.amount,
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
                    "details": a.details,
                    "created_at": a.created_at.isoformat(),
                }
                for a in audits
            ],
        },
    }

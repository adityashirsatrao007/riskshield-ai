from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import verify_api_key
from app.core.database import get_db
from app.models.transaction import Transaction

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/dashboard")
async def dashboard_stats(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    total = (await db.execute(select(func.count(Transaction.id)))).scalar()
    flagged = (await db.execute(
        select(func.count(Transaction.id)).where(Transaction.is_flagged.is_(True))
    )).scalar()
    avg_score = (await db.execute(
        select(func.avg(Transaction.risk_score))
    )).scalar() or 0

    high_risk_value = (await db.execute(
        select(func.sum(Transaction.amount)).where(
            Transaction.risk_level.in_(["high", "critical"])
        )
    )).scalar() or 0

    fraud_rate = (flagged / total * 100) if total > 0 else 0

    return {
        "success": True,
        "data": {
            "total_transactions": total,
            "flagged_transactions": flagged,
            "fraud_rate": round(fraud_rate, 2),
            "avg_risk_score": round(float(avg_score), 4),
            "potential_savings": round(float(high_risk_value), 2),
        },
    }


@router.get("/timeline")
async def timeline(
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    result = await db.execute(
        select(
            func.date(Transaction.timestamp).label("date"),
            func.count(Transaction.id).label("total"),
            func.sum(case((Transaction.is_flagged == True, 1), else_=0)).label("flagged"),
            func.avg(Transaction.risk_score).label("avg_score"),
        )
        .where(Transaction.timestamp >= cutoff)
        .group_by(func.date(Transaction.timestamp))
        .order_by(func.date(Transaction.timestamp))
    )
    rows = result.all()

    return {
        "success": True,
        "data": [
            {
                "date": str(r.date),
                "total": r.total,
                "flagged": int(r.flagged or 0),
                "avg_score": round(float(r.avg_score or 0), 4),
            }
            for r in rows
        ],
    }


@router.get("/risk-distribution")
async def risk_distribution(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    buckets = [
        ("low", 0.0, 0.3),
        ("medium", 0.3, 0.6),
        ("high", 0.6, 0.8),
        ("critical", 0.8, 1.01),
    ]
    distribution = {}
    for label, low, high in buckets:
        count = (await db.execute(
            select(func.count(Transaction.id)).where(
                Transaction.risk_score >= low,
                Transaction.risk_score < high,
            )
        )).scalar()
        distribution[label] = count

    return {"success": True, "data": distribution}


@router.get("/false-positive-analysis")
async def false_positive_analysis(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    avg_txn = (await db.execute(select(func.avg(Transaction.amount)))).scalar() or 0
    total_flagged = (await db.execute(
        select(func.count(Transaction.id)).where(Transaction.is_flagged.is_(True))
    )).scalar()
    resolved = (await db.execute(
        select(func.count(Transaction.id)).where(
            Transaction.is_flagged.is_(True),
            Transaction.is_resolved.is_(True),
        )
    )).scalar()
    false_positives = total_flagged - resolved

    avg_value = float(avg_txn)
    estimated_fp_cost = false_positives * avg_value
    estimated_savings = resolved * avg_value

    return {
        "success": True,
        "data": {
            "total_flagged": total_flagged,
            "resolved": resolved,
            "estimated_false_positives": false_positives,
            "average_transaction_value": round(avg_value, 2),
            "estimated_fp_cost": round(estimated_fp_cost, 2),
            "estimated_savings": round(estimated_savings, 2),
            "net_benefit": round(estimated_savings - estimated_fp_cost, 2),
        },
    }

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, desc, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.auth import verify_api_key
from app.models.transaction import Alert
from app.api.schemas import AlertUpdate

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("")
async def list_alerts(
    status: str = None,
    risk_level: str = None,
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    query = select(Alert)
    count_query = select(func.count(Alert.id))

    if status:
        query = query.where(Alert.status == status)
        count_query = count_query.where(Alert.status == status)
    if risk_level:
        query = query.where(Alert.risk_level == risk_level)
        count_query = count_query.where(Alert.risk_level == risk_level)

    total = (await db.execute(count_query)).scalar()
    result = await db.execute(
        query.order_by(desc(Alert.created_at)).offset(offset).limit(limit)
    )
    alerts = result.scalars().all()

    return {
        "success": True,
        "data": [
            {
                "id": a.id,
                "transaction_id": a.transaction_id,
                "risk_score": a.risk_score,
                "risk_level": a.risk_level,
                "explanation": a.explanation,
                "status": a.status,
                "created_at": a.created_at.isoformat(),
                "updated_at": a.updated_at.isoformat() if a.updated_at else None,
            }
            for a in alerts
        ],
        "total": total,
        "offset": offset,
        "limit": limit,
    }


@router.put("/{alert_id}/status")
async def update_alert_status(
    alert_id: int,
    body: AlertUpdate,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    if body.status not in ("open", "acknowledged", "dismissed", "resolved"):
        raise HTTPException(status_code=400, detail="Invalid status")

    result = await db.execute(select(Alert).where(Alert.id == alert_id))
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    alert.status = body.status
    alert.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(alert)

    return {
        "success": True,
        "data": {
            "id": alert.id,
            "status": alert.status,
            "updated_at": alert.updated_at.isoformat(),
        },
    }


@router.get("/stats")
async def alert_stats(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
):
    total = (await db.execute(select(func.count(Alert.id)))).scalar()
    by_status = (await db.execute(
        select(Alert.status, func.count(Alert.id)).group_by(Alert.status)
    )).all()
    by_risk = (await db.execute(
        select(Alert.risk_level, func.count(Alert.id)).group_by(Alert.risk_level)
    )).all()

    return {
        "success": True,
        "data": {
            "total": total,
            "by_status": {s: c for s, c in by_status},
            "by_risk_level": {r: c for r, c in by_risk},
        },
    }

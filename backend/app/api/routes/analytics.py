from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from app.models.schemas import AnalyticsRequest
from app.services.analytics.engine import analytics_engine

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.post("/trend")
async def trend(req: AnalyticsRequest):
    try:
        result = analytics_engine.trend_analysis(
            req.variable, str(req.start_date), str(req.end_date),
            req.latitude, req.longitude
        )
        return {"analysis_type": "trend", "variable": req.variable,
                "start_date": str(req.start_date), "end_date": str(req.end_date),
                "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/anomaly")
async def anomaly(req: AnalyticsRequest,
                   threshold: float = Query(2.0)):
    try:
        result = analytics_engine.anomaly_detection(
            req.variable, str(req.start_date), str(req.end_date),
            req.latitude, req.longitude, threshold
        )
        return {"analysis_type": "anomaly", "variable": req.variable,
                "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/risk")
async def risk(req: AnalyticsRequest):
    try:
        result = analytics_engine.risk_assessment(
            str(req.start_date), str(req.end_date),
            req.latitude, req.longitude
        )
        return {"analysis_type": "risk", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/indicators")
async def indicators(
    start: str = Query("2025-01-01"),
    end:   str = Query("2025-12-31"),
):
    try:
        result = analytics_engine.climate_indicators(start, end)
        return {"analysis_type": "indicators", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

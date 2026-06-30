from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List
from app.services.digital_twin import digital_twin

router = APIRouter(prefix="/climate-state", tags=["Climate State"])


@router.get("/current")
async def current_state(
    date: str = Query(..., description="Date in YYYY-MM-DD format"),
    variable: str = Query("rainfall", description="rainfall | max_temp | min_temp"),
    bbox: Optional[str] = Query(None, description="lon_min,lat_min,lon_max,lat_max"),
):
    bbox_list = [float(x) for x in bbox.split(",")] if bbox else None
    try:
        return digital_twin.get_current_state(date, variable, bbox_list)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/latest")
async def latest_state(
    variable: str = Query("rainfall"),
):
    return digital_twin.get_latest_state(variable)


@router.get("/timeseries")
async def timeseries(
    lat: float = Query(...),
    lon: float = Query(...),
    start: str = Query("2025-01-01"),
    end:   str = Query("2025-12-31"),
):
    try:
        return digital_twin.get_state_timeseries(lat, lon, start, end)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/national-summary")
async def national_summary(
    date: Optional[str] = Query(None),
):
    return digital_twin.get_national_summary(date)

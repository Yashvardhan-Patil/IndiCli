from fastapi import APIRouter, HTTPException, BackgroundTasks
from app.models.schemas import ForecastRequest, ForecastResponse, GridForecastRequest
from app.services.forecasting.ensemble import ensemble_forecaster
from app.services.dataset_manager import get_dataset_manager
from datetime import datetime
import pandas as pd

router = APIRouter(prefix="/forecast", tags=["Forecasting"])


@router.post("/point")
async def forecast_point(req: ForecastRequest):
    try:
        df = ensemble_forecaster.forecast_point(req.latitude, req.longitude,
                                                 req.horizon_days)
        forecasts = []
        for _, row in df.iterrows():
            forecasts.append({
                "target_date":   str(row["target_date"].date()) if hasattr(row["target_date"], "date") else str(row["target_date"]),
                "rainfall_pred": row.get("rainfall_pred"),
                "max_temp_pred": row.get("max_temp_pred"),
                "min_temp_pred": row.get("min_temp_pred"),
                "confidence":    row.get("confidence", 0.5),
            })
        return {
            "latitude":             req.latitude,
            "longitude":            req.longitude,
            "model":                req.model.value,
            "forecast_generated_at":datetime.utcnow().isoformat(),
            "horizon_days":         req.horizon_days,
            "forecasts":            forecasts,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/grid")
async def forecast_grid(
    date: str,
    variable: str = "rainfall",
    horizon_days: int = 7,
):
    """Return ensemble forecast grid for a given target date."""
    try:
        dm = get_dataset_manager()
        # Get all unique lat/lon in dataset and forecast each
        locs = dm.get_unique_locations(limit=200)
        records = []
        for _, loc in locs.iterrows():
            df = ensemble_forecaster.forecast_point(
                float(loc["latitude"]), float(loc["longitude"]), horizon_days
            )
            if not df.empty:
                row = df.iloc[0]
                records.append({
                    "latitude":  float(loc["latitude"]),
                    "longitude": float(loc["longitude"]),
                    "value":     row.get(f"{variable}_pred") or row.get("rainfall_pred"),
                    "confidence":row.get("confidence", 0.5),
                })
        return {"date": date, "variable": variable, "grid": records}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/train")
async def train_models(background_tasks: BackgroundTasks):
    """Trigger background model training."""
    def _train():
        metrics = ensemble_forecaster.train_all()
        return metrics
    background_tasks.add_task(_train)
    return {"status": "training_started",
            "message": "Model training started in background."}

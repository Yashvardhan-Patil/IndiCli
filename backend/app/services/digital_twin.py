"""
Digital Twin Core Engine
Maintains three parallel climate states: current, forecast, scenario.
"""

import pandas as pd
import numpy as np
from datetime import date, timedelta
from typing import Optional, Dict, Any
import structlog

from app.services.dataset_manager import get_dataset_manager
from app.core.config import get_settings

log = structlog.get_logger("digital_twin")

VARIABLES = ["rainfall", "max_temp", "min_temp"]


class DigitalTwinEngine:
    """
    Stateless engine — reads from the dataset and forecast cache
    to serve current, predicted, and scenario climate states.
    """

    def get_current_state(self, query_date: str, variable: str,
                           bbox: Optional[list] = None) -> Dict[str, Any]:
        dm  = get_dataset_manager()
        df  = dm.get_grid_for_date(query_date, variable, bbox)
        stats = _compute_stats(df[variable])
        return {
            "state_type": "current",
            "date": query_date,
            "variable": variable,
            "grid_points": df.rename(columns={variable: "value"}).to_dict("records"),
            "stats": stats,
        }

    def get_latest_state(self, variable: str = "rainfall") -> Dict[str, Any]:
        dm = get_dataset_manager()
        latest_date = str(dm.get_latest_date().date())
        return self.get_current_state(latest_date, variable)

    def get_state_timeseries(self, lat: float, lon: float,
                              start: str, end: str) -> Dict[str, Any]:
        dm  = get_dataset_manager()
        df  = dm.get_timeseries(lat, lon, start, end)
        return {
            "latitude": lat,
            "longitude": lon,
            "dates": [str(d.date()) for d in df["date"]],
            "rainfall":  df["rainfall"].where(df["rainfall"].notna(), None).tolist(),
            "max_temp":  df["max_temp"].where(df["max_temp"].notna(), None).tolist(),
            "min_temp":  df["min_temp"].where(df["min_temp"].notna(), None).tolist(),
        }

    def get_national_summary(self, query_date: Optional[str] = None) -> Dict[str, Any]:
        dm = get_dataset_manager()
        if query_date:
            df = dm.get_data_for_range(query_date, query_date)
        else:
            df = dm.get_national_daily_averages()

        summary = {}
        for v in VARIABLES:
            if v in df.columns:
                col = df[v].dropna()
                summary[v] = {
                    "mean":   round(float(col.mean()), 3) if len(col) else None,
                    "max":    round(float(col.max()),  3) if len(col) else None,
                    "min":    round(float(col.min()),  3) if len(col) else None,
                    "p90":    round(float(col.quantile(0.9)), 3) if len(col) else None,
                }
            else:
                summary[v] = {"mean": None, "max": None, "min": None, "p90": None}

        # Monthly aggregates
        query_monthly = """
            SELECT EXTRACT(MONTH FROM date)::int as month,
                   AVG(rainfall) as rainfall,
                   AVG(max_temp) as max_temp,
                   AVG(min_temp) as min_temp
            FROM climate_records
            GROUP BY month
            ORDER BY month
        """
        monthly_df = pd.read_sql(query_monthly, dm.engine)
        
        monthly_dict = {v: {} for v in VARIABLES}
        for _, row in monthly_df.iterrows():
            m = int(row["month"])
            monthly_dict["rainfall"][m] = round(float(row["rainfall"]), 3) if not pd.isna(row["rainfall"]) else None
            monthly_dict["max_temp"][m] = round(float(row["max_temp"]), 3) if not pd.isna(row["max_temp"]) else None
            monthly_dict["min_temp"][m] = round(float(row["min_temp"]), 3) if not pd.isna(row["min_temp"]) else None
            
        summary["monthly_avg"] = monthly_dict

        return summary


def _compute_stats(series: pd.Series) -> dict:
    s = series.dropna()
    if s.empty:
        return {}
    return {
        "mean": round(float(s.mean()), 3),
        "max":  round(float(s.max()),  3),
        "min":  round(float(s.min()),  3),
        "std":  round(float(s.std()),  3),
        "p90":  round(float(s.quantile(0.9)), 3),
        "count": int(len(s)),
    }


digital_twin = DigitalTwinEngine()

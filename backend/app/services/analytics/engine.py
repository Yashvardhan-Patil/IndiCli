"""
Climate Analytics Engine
Provides: trend analysis, anomaly detection, risk assessment, climate indicators.
"""

import pandas as pd
import numpy as np
from scipy import stats
from typing import Optional, Dict, Any
import structlog

from app.services.dataset_manager import get_dataset_manager

log = structlog.get_logger("analytics")


class AnalyticsEngine:

    # ── Trend Analysis ────────────────────────────────────────────────────────

    def trend_analysis(self, variable: str, start: str, end: str,
                        lat: Optional[float] = None,
                        lon: Optional[float] = None) -> Dict[str, Any]:
        df = self._get_series(variable, start, end, lat, lon)
        if df.empty:
            return {}

        daily = df.groupby("date")[variable].mean().reset_index()
        daily = daily.sort_values("date")
        y     = daily[variable].fillna(method="ffill").values
        x     = np.arange(len(y))

        slope, intercept, r_val, p_val, _ = stats.linregress(x, y)
        trend_line = slope * x + intercept
        ma30 = pd.Series(y).rolling(30, min_periods=1).mean().tolist()

        return {
            "dates":          [str(d.date()) for d in daily["date"]],
            "values":         [round(float(v), 3) if not np.isnan(v) else None for v in y],
            "trend_slope":    round(float(slope), 6),
            "trend_r2":       round(float(r_val**2), 4),
            "trend_line":     [round(float(v), 3) for v in trend_line],
            "moving_avg_30d": [round(float(v), 3) if not np.isnan(v) else None for v in ma30],
            "p_value":        round(float(p_val), 6),
        }

    # ── Anomaly Detection ─────────────────────────────────────────────────────

    def anomaly_detection(self, variable: str, start: str, end: str,
                           lat: Optional[float] = None,
                           lon: Optional[float] = None,
                           threshold_sigma: float = 2.0) -> Dict[str, Any]:
        df    = self._get_series(variable, start, end, lat, lon)
        daily = df.groupby("date")[variable].mean().reset_index().sort_values("date")
        y     = daily[variable].fillna(method="ffill").values

        mean, std = float(np.nanmean(y)), float(np.nanstd(y))
        z_scores  = (y - mean) / (std + 1e-6)
        flags     = np.abs(z_scores) > threshold_sigma

        return {
            "dates":          [str(d.date()) for d in daily["date"]],
            "values":         [round(float(v), 3) if not np.isnan(v) else None for v in y],
            "anomaly_scores": [round(float(z), 3) for z in z_scores],
            "anomaly_flags":  flags.tolist(),
            "threshold":      threshold_sigma,
            "mean":           round(mean, 3),
            "std":            round(std,  3),
            "anomaly_count":  int(flags.sum()),
        }

    # ── Risk Assessment ───────────────────────────────────────────────────────

    def risk_assessment(self, start: str, end: str,
                         lat: Optional[float] = None,
                         lon: Optional[float] = None) -> Dict[str, Any]:
        df = self._get_series("rainfall", start, end, lat, lon)
        if df.empty:
            return {}

        df2 = df.merge(
            self._get_series("max_temp", start, end, lat, lon),
            on=["date","latitude","longitude"], how="outer"
        )

        rf   = df2["rainfall"].dropna()
        tmax = df2["max_temp"].dropna() if "max_temp" in df2 else pd.Series(dtype=float)

        # Risk scores (0–1 normalized)
        drought_risk   = float(np.clip((rf == 0).mean() * 1.5, 0, 1))
        flood_risk     = float(np.clip(((rf > rf.quantile(0.95)).mean()) * 2.5, 0, 1))
        heatwave_risk  = float(np.clip((tmax > 40).mean() * 2.0, 0, 1)) if len(tmax) else 0.0
        cold_wave_risk = float(np.clip((df2.get("min_temp", pd.Series([15])) < 5).mean(), 0, 1))
        composite_risk = round((drought_risk + flood_risk + heatwave_risk + cold_wave_risk) / 4, 3)

        if composite_risk > 0.6:
            level = "HIGH"
        elif composite_risk > 0.3:
            level = "MEDIUM"
        else:
            level = "LOW"

        return {
            "drought_risk":   round(drought_risk,   3),
            "flood_risk":     round(flood_risk,     3),
            "heatwave_risk":  round(heatwave_risk,  3),
            "cold_wave_risk": round(cold_wave_risk, 3),
            "composite_risk": composite_risk,
            "risk_level":     level,
        }

    # ── Climate Indicators ────────────────────────────────────────────────────

    def climate_indicators(self, start: str, end: str) -> Dict[str, Any]:
        dm  = get_dataset_manager()
        daily = dm.get_national_daily_averages_for_range(start, end)

        monsoon   = daily[daily["date"].dt.month.isin([6,7,8,9])]
        pre_mon   = daily[daily["date"].dt.month.isin([3,4,5])]

        return {
            "annual_rainfall_mm":        round(float(daily["rainfall"].sum()), 2),
            "monsoon_rainfall_mm":        round(float(monsoon["rainfall"].sum()), 2),
            "monsoon_contribution_pct":   round(
                100 * float(monsoon["rainfall"].sum()) /
                (float(daily["rainfall"].sum()) + 1e-6), 2
            ),
            "mean_max_temp":              round(float(daily["max_temp"].mean()), 2),
            "mean_min_temp":              round(float(daily["min_temp"].mean()), 2),
            "days_above_40c":             int((daily["max_temp"] > 40).sum()),
            "days_below_5c":              int((daily["min_temp"] < 5).sum()),
            "consecutive_dry_days":       int(_max_consecutive(daily["rainfall"] < 0.5)),
            "consecutive_wet_days":       int(_max_consecutive(daily["rainfall"] >= 1.0)),
            "diurnal_temp_range":         round(
                float((daily["max_temp"] - daily["min_temp"]).mean()), 2
            ),
        }

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _get_series(self, variable: str, start: str, end: str,
                     lat: Optional[float], lon: Optional[float]) -> pd.DataFrame:
        dm = get_dataset_manager()
        if lat is not None and lon is not None:
            df = dm.get_timeseries(lat, lon, start, end)
        else:
            df = dm.get_data_for_range(start, end)
        return df[[c for c in ["date","latitude","longitude", variable] if c in df.columns]]


def _max_consecutive(bool_series: pd.Series) -> int:
    """Max run of True values."""
    max_run = cur = 0
    for v in bool_series:
        if v:
            cur += 1
            max_run = max(max_run, cur)
        else:
            cur = 0
    return max_run


analytics_engine = AnalyticsEngine()

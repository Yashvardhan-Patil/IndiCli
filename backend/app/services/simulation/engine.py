"""
What-If Simulation Engine
Applies physical perturbations to baseline climate data for scenario analysis.
"""

import pandas as pd
import numpy as np
import uuid
from datetime import date
from typing import Optional, Dict, Any
import structlog

from app.services.dataset_manager import get_dataset_manager

log = structlog.get_logger("simulation")

# Scenario delta definitions
SCENARIO_DELTAS: Dict[str, Dict[str, Any]] = {
    "temp_plus_1c":     {"max_temp": +1.0, "min_temp": +1.0, "rainfall": 0.0},
    "temp_plus_2c":     {"max_temp": +2.0, "min_temp": +2.0, "rainfall": 0.0},
    "rain_plus_20pct":  {"max_temp": 0.0,  "min_temp": 0.0,  "rainfall": +0.20},
    "rain_minus_20pct": {"max_temp": 0.0,  "min_temp": 0.0,  "rainfall": -0.20},
    "drought":          {"max_temp": +1.5, "min_temp": +0.8, "rainfall": -0.70},
    "heatwave":         {"max_temp": +5.0, "min_temp": +3.0, "rainfall": -0.50},
    "extreme_rainfall": {"max_temp": -1.0, "min_temp": -0.5, "rainfall": +2.00},
}

SCENARIO_DESCRIPTIONS = {
    "temp_plus_1c":     "+1 degree C uniform temperature increase across India",
    "temp_plus_2c":     "+2 degree C uniform temperature increase across India",
    "rain_plus_20pct":  "+20% rainfall increase (wetter scenario)",
    "rain_minus_20pct": "-20% rainfall reduction (drier scenario)",
    "drought":          "Severe drought: -70% rainfall, +1.5 C temperature",
    "heatwave":         "Heatwave event: +5 C max temp, -50% rainfall",
    "extreme_rainfall": "Extreme rainfall: +200% rainfall, -1 C temperature",
}


class SimulationEngine:

    def run_scenario(self,
                     scenario_type: str,
                     base_date: str,
                     duration_days: int = 30,
                     bbox: Optional[list] = None) -> Dict[str, Any]:

        if scenario_type not in SCENARIO_DELTAS:
            raise ValueError(f"Unknown scenario: {scenario_type}")

        dm     = get_dataset_manager()
        deltas = SCENARIO_DELTAS[scenario_type]

        # Pull baseline data
        end_date = (pd.Timestamp(base_date) + pd.Timedelta(days=duration_days) - pd.Timedelta(days=1)).strftime("%Y-%m-%d")
        df = dm.get_data_for_range(base_date, end_date, bbox=bbox)

        if df.empty:
            raise ValueError("No data for the given date/bbox range.")

        scenario_id = f"{scenario_type}_{uuid.uuid4().hex[:8]}"

        # Apply deltas
        df_s = df.copy()
        for var, delta in deltas.items():
            if var not in df_s.columns:
                continue
            if var == "rainfall":
                if delta == 0.0:
                    pass
                elif delta > 0:
                    # Additive + multiplicative for rainfall
                    df_s[var] = df_s[var].fillna(0) * (1 + delta)
                else:
                    df_s[var] = (df_s[var].fillna(0) * (1 + delta)).clip(lower=0)
            else:
                df_s[var] = df_s[var] + delta

        # Compute deltas per row
        df_s["delta_rainfall"]  = (df_s["rainfall"]  - df["rainfall"])
        df_s["delta_max_temp"]  = (df_s["max_temp"]   - df["max_temp"])
        df_s["delta_min_temp"]  = (df_s["min_temp"]   - df["min_temp"])

        # Summary stats
        summary: Dict[str, Any] = {}
        for v in ["rainfall", "max_temp", "min_temp"]:
            baseline_mean = float(df[v].mean())   if not df[v].isna().all()   else 0.0
            scenario_mean = float(df_s[v].mean()) if not df_s[v].isna().all() else 0.0
            summary[v] = {
                "baseline_mean": round(baseline_mean, 3),
                "scenario_mean": round(scenario_mean, 3),
                "absolute_change": round(scenario_mean - baseline_mean, 3),
                "pct_change": round(
                    100 * (scenario_mean - baseline_mean) / (abs(baseline_mean) + 1e-6), 2
                ),
            }

        # Aggregate to daily grid for output (limit payload)
        daily_grid = (
            df_s.groupby(["date", "latitude", "longitude"])[
                ["rainfall","max_temp","min_temp",
                 "delta_rainfall","delta_max_temp","delta_min_temp"]
            ].mean()
            .reset_index()
        )

        grid_records = []
        for _, row in daily_grid.head(5000).iterrows():
            grid_records.append({
                "latitude":      round(float(row["latitude"]),  3),
                "longitude":     round(float(row["longitude"]), 3),
                "rainfall":      _safe(row["rainfall"]),
                "max_temp":      _safe(row["max_temp"]),
                "min_temp":      _safe(row["min_temp"]),
                "delta_rainfall":_safe(row["delta_rainfall"]),
                "delta_max_temp":_safe(row["delta_max_temp"]),
                "delta_min_temp":_safe(row["delta_min_temp"]),
            })

        log.info("Scenario run", scenario=scenario_type,
                 rows=len(df), scenario_id=scenario_id)

        return {
            "scenario_id":   scenario_id,
            "scenario_type": scenario_type,
            "base_date":     base_date,
            "duration_days": duration_days,
            "description":   SCENARIO_DESCRIPTIONS[scenario_type],
            "grid_points":   grid_records,
            "summary_stats": summary,
        }


def _safe(val) -> Optional[float]:
    if pd.isna(val):
        return None
    return round(float(val), 3)


simulation_engine = SimulationEngine()

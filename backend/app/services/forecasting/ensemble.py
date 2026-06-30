"""
Hybrid Ensemble Forecasting Engine
Fuses XGBoost + LSTM predictions with weighted averaging and confidence scoring.
"""

import numpy as np
import pandas as pd
from typing import Optional
import structlog

from app.services.forecasting.xgboost_model import XGBoostForecaster, xgb_forecaster
from app.services.forecasting.lstm_model import LSTMForecaster, lstm_forecaster
from app.services.dataset_manager import get_dataset_manager
from app.core.config import get_settings

log = structlog.get_logger("ensemble_forecaster")

TARGETS = ["rainfall", "max_temp", "min_temp"]


def _confidence_score(xgb_pred: pd.Series, lstm_pred: pd.Series,
                       std_history: float, horizon_day: int) -> float:
    """
    Confidence decays with forecast horizon and disagreement between models.
    """
    agreement = 1.0 - min(abs(float(xgb_pred) - float(lstm_pred)) /
                           (std_history + 1e-6), 1.0)
    decay     = np.exp(-0.015 * (horizon_day - 1))
    return round(float(np.clip(agreement * decay, 0.05, 0.99)), 3)


class EnsembleForecaster:
    def __init__(self):
        self.settings   = get_settings()
        self.w_xgb      = self.settings.ENSEMBLE_WEIGHTS_XGBOOST
        self.w_lstm     = self.settings.ENSEMBLE_WEIGHTS_LSTM
        self._trained   = False

    def _ensure_trained(self):
        if self._trained:
            return
        # Try loading persisted models
        xgb_ok  = xgb_forecaster.load()
        lstm_ok = lstm_forecaster.load()
        if xgb_ok and lstm_ok:
            self._trained = True
            log.info("Loaded persisted models")
            return
        # Train from scratch
        log.info("Training models from dataset ...")
        dm  = get_dataset_manager()
        # Use India-level daily aggregates for point forecast training
        daily = dm.get_national_daily_averages()
        xgb_metrics  = xgb_forecaster.train(daily)
        lstm_metrics = lstm_forecaster.train(daily)
        self._trained = True
        log.info("Models trained", xgb=xgb_metrics, lstm=lstm_metrics)

    def forecast_point(self, lat: float, lon: float,
                        horizon: int = 30) -> pd.DataFrame:
        self._ensure_trained()
        dm   = get_dataset_manager()
        hist = dm.get_timeseries(lat, lon, "2025-01-01", "2025-12-31")

        # Ensure we have enough valid (non-NaN) history rows for the LSTM model
        valid_hist_rows = hist[TARGETS].dropna().shape[0]
        if valid_hist_rows < self.settings.LSTM_LOOKBACK_DAYS:
            # Fall back to national average
            hist = dm.get_national_daily_averages()

        xgb_preds  = xgb_forecaster.predict_point(hist, horizon)
        lstm_preds = lstm_forecaster.predict_point(hist)
        lstm_preds = lstm_preds.head(horizon)

        std_rf  = float(hist["rainfall"].std())  if "rainfall"  in hist else 5.0
        std_tx  = float(hist["max_temp"].std())  if "max_temp"  in hist else 3.0
        std_tn  = float(hist["min_temp"].std())  if "min_temp"  in hist else 3.0
        stds    = {"rainfall": std_rf, "max_temp": std_tx, "min_temp": std_tn}

        records = []
        for i in range(min(len(xgb_preds), len(lstm_preds))):
            xr = xgb_preds.iloc[i]
            lr = lstm_preds.iloc[i]
            row = {"target_date": xr["date"]}
            conf_sum = 0.0
            for t, out_key in [("rainfall","rainfall_pred"),
                                ("max_temp","max_temp_pred"),
                                ("min_temp","min_temp_pred")]:
                xv = xr.get(t) or 0.0
                lv = lr.get(t) or 0.0
                fused = self.w_xgb * xv + self.w_lstm * lv
                if t == "rainfall":
                    fused = max(0.0, fused)
                row[out_key] = round(float(fused), 3)
                conf_sum += _confidence_score(xv, lv, stds[t], i + 1)
            row["confidence"] = round(conf_sum / 3, 3)
            records.append(row)

        return pd.DataFrame(records)

    def train_all(self) -> dict:
        dm  = get_dataset_manager()
        daily = dm.get_national_daily_averages()
        xgb_m  = xgb_forecaster.train(daily)
        lstm_m = lstm_forecaster.train(daily)
        self._trained = True
        return {"xgboost": xgb_m, "lstm": lstm_m}


ensemble_forecaster = EnsembleForecaster()

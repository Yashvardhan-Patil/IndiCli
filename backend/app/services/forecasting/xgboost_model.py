"""
XGBoost Forecaster
Trains separate XGBoost models for rainfall, max_temp, min_temp.
Uses lag features, rolling statistics, and calendar features.
"""

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, r2_score
import joblib
from pathlib import Path
from typing import Optional
import structlog

log = structlog.get_logger("xgboost_forecaster")


def build_features(df: pd.DataFrame, target: str,
                   lags: list = None) -> pd.DataFrame:
    lags = lags or [1, 2, 3, 7, 14, 30]
    df = df.sort_values("date").copy()
    df["doy"]   = df["date"].dt.dayofyear
    df["month"] = df["date"].dt.month
    df["week"]  = df["date"].dt.isocalendar().week.astype(int)
    df["sin_doy"] = np.sin(2 * np.pi * df["doy"] / 365)
    df["cos_doy"] = np.cos(2 * np.pi * df["doy"] / 365)

    for lag in lags:
        df[f"{target}_lag{lag}"] = df[target].shift(lag)
    df[f"{target}_roll7"]  = df[target].shift(1).rolling(7,  min_periods=1).mean()
    df[f"{target}_roll30"] = df[target].shift(1).rolling(30, min_periods=1).mean()
    df[f"{target}_std7"]   = df[target].shift(1).rolling(7,  min_periods=1).std()

    # Cross-variable lags
    for other in ["rainfall", "max_temp", "min_temp"]:
        if other != target and other in df.columns:
            df[f"{other}_lag1"] = df[other].shift(1)

    df = df.dropna()
    return df


class XGBoostForecaster:
    TARGETS = ["rainfall", "max_temp", "min_temp"]

    def __init__(self, n_estimators: int = 200, model_dir: str = "./models"):
        self.n_estimators = n_estimators
        self.model_dir    = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)
        self.models  : dict = {}
        self.scalers : dict = {}
        self.feat_cols: dict = {}
        self._trained = False

    def _get_xy(self, df: pd.DataFrame, target: str):
        feat_df = build_features(df[["date", target] + [
            c for c in ["rainfall","max_temp","min_temp"] if c != target and c in df.columns
        ]].copy(), target)
        drop = {"date", target} | {c for c in feat_df.columns if c in ["rainfall","max_temp","min_temp"]}
        feat_cols = [c for c in feat_df.columns if c not in drop]
        X = feat_df[feat_cols].values
        y = feat_df[target].values
        return X, y, feat_cols, feat_df["date"]

    def train(self, df: pd.DataFrame) -> dict:
        metrics = {}
        for target in self.TARGETS:
            if target not in df.columns:
                continue
            sub = df[["date"] + [
                c for c in ["rainfall","max_temp","min_temp"] if c in df.columns
            ]].dropna(subset=[target])

            X, y, feat_cols, dates = self._get_xy(sub, target)

            # 80/20 temporal split
            split  = int(len(X) * 0.8)
            X_tr, X_te = X[:split], X[split:]
            y_tr, y_te = y[:split], y[split:]

            model = xgb.XGBRegressor(
                n_estimators=self.n_estimators,
                learning_rate=0.05,
                max_depth=6,
                subsample=0.8,
                colsample_bytree=0.8,
                objective="reg:squarederror",
                random_state=42,
                n_jobs=-1,
            )
            model.fit(X_tr, y_tr,
                      eval_set=[(X_te, y_te)],
                      verbose=False)

            preds = model.predict(X_te)
            if target == "rainfall":
                preds = np.clip(preds, 0, None)

            mae = mean_absolute_error(y_te, preds)
            r2  = r2_score(y_te, preds)
            metrics[target] = {"mae": round(mae, 4), "r2": round(r2, 4)}

            self.models[target]   = model
            self.feat_cols[target] = feat_cols
            joblib.dump(model, self.model_dir / f"xgb_{target}.pkl")
            log.info("XGBoost trained", target=target, mae=mae, r2=r2)

        # Save feature column names so they can be restored on load
        joblib.dump(self.feat_cols, self.model_dir / "xgb_feat_cols.pkl")
        self._trained = True
        return metrics

    def load(self) -> bool:
        ok = True
        for target in self.TARGETS:
            p = self.model_dir / f"xgb_{target}.pkl"
            if p.exists():
                self.models[target] = joblib.load(p)
            else:
                ok = False
        # Restore feature column names (required for predict_point)
        # If missing, predict_point() will regenerate them on the fly
        feat_cols_path = self.model_dir / "xgb_feat_cols.pkl"
        if feat_cols_path.exists():
            self.feat_cols = joblib.load(feat_cols_path)
        self._trained = ok
        return ok

    def predict_point(self, history_df: pd.DataFrame,
                      horizon: int = 30) -> pd.DataFrame:
        """Recursive multi-step forecast for a single location."""
        if not self._trained:
            raise RuntimeError("Models not trained. Call train() first.")

        df = history_df[["date","rainfall","max_temp","min_temp"]].copy()
        df = df.sort_values("date").reset_index(drop=True)
        last_date = df["date"].max()
        future_dates = pd.date_range(last_date + pd.Timedelta(days=1),
                                     periods=horizon, freq="D")
        preds_out = []
        for fd in future_dates:
            row = {"date": fd}
            for target in self.TARGETS:
                if target not in self.models:
                    row[target] = None
                    continue
                feat_df = build_features(df[["date"] + self.TARGETS].copy(), target)
                if feat_df.empty:
                    row[target] = None
                    continue
                # Fallback: if feat_cols not loaded (e.g. old models), compute on the fly
                feat_cols = self.feat_cols.get(target)
                if feat_cols is None:
                    # Regenerate by dropping target/original columns from feature df
                    drop = {"date", target} | {
                        c for c in feat_df.columns
                        if c in ["rainfall","max_temp","min_temp"]
                    }
                    feat_cols = [c for c in feat_df.columns if c not in drop]
                    self.feat_cols[target] = feat_cols
                last_feat = feat_df[feat_cols].iloc[[-1]].values
                pred = float(self.models[target].predict(last_feat)[0])
                if target == "rainfall":
                    pred = max(0.0, pred)
                row[target] = round(pred, 3)
            # Append prediction to history for next step
            new_row = pd.DataFrame([{"date": fd, "rainfall": row.get("rainfall"),
                                      "max_temp": row.get("max_temp"),
                                      "min_temp": row.get("min_temp")}])
            df = pd.concat([df, new_row], ignore_index=True)
            preds_out.append(row)
        return pd.DataFrame(preds_out)


xgb_forecaster = XGBoostForecaster()

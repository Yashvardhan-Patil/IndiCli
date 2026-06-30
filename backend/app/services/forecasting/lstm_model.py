"""
LSTM Forecaster
Sequence-to-sequence LSTM for multi-variable climate time-series forecasting.
"""

import numpy as np
import pandas as pd
import joblib
from pathlib import Path
from typing import Optional
import structlog

log = structlog.get_logger("lstm_forecaster")

FEATURES = ["rainfall", "max_temp", "min_temp", "sin_doy", "cos_doy"]
TARGETS  = ["rainfall", "max_temp", "min_temp"]


def add_calendar_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    doy = df["date"].dt.dayofyear
    df["sin_doy"] = np.sin(2 * np.pi * doy / 365).astype(np.float32)
    df["cos_doy"] = np.cos(2 * np.pi * doy / 365).astype(np.float32)
    return df


def make_sequences(data: np.ndarray, lookback: int, horizon: int):
    X, y = [], []
    for i in range(lookback, len(data) - horizon + 1):
        X.append(data[i - lookback:i])
        y.append(data[i:i + horizon, :3])   # first 3 cols = targets
    return np.array(X, dtype=np.float32), np.array(y, dtype=np.float32)


class LSTMForecaster:
    def __init__(self, lookback: int = 60, horizon: int = 30,
                 model_dir: str = "./models"):
        self.lookback  = lookback
        self.horizon   = horizon
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)
        self.model   = None
        self.scaler  = None
        self._trained = False

    def _build_model(self, n_features: int):
        try:
            import tensorflow as tf
            from tensorflow.keras import layers, Model, Input
        except ImportError:
            raise RuntimeError("TensorFlow not installed.")

        inp = Input(shape=(self.lookback, n_features))
        x   = layers.LSTM(128, return_sequences=True)(inp)
        x   = layers.Dropout(0.2)(x)
        x   = layers.LSTM(64)(x)
        x   = layers.Dropout(0.2)(x)
        x   = layers.Dense(64, activation="relu")(x)
        out = layers.Dense(self.horizon * 3)(x)
        out = layers.Reshape((self.horizon, 3))(out)
        model = Model(inp, out)
        model.compile(optimizer="adam", loss="mse",
                      metrics=["mae"])
        return model

    def train(self, df: pd.DataFrame, epochs: int = 50) -> dict:
        from sklearn.preprocessing import MinMaxScaler

        df = df.sort_values("date").reset_index(drop=True)
        df = add_calendar_features(df)
        df = df[["date"] + FEATURES].dropna()

        scaler = MinMaxScaler()
        scaled = scaler.fit_transform(df[FEATURES].values)
        self.scaler = scaler
        joblib.dump(scaler, self.model_dir / "lstm_scaler.pkl")

        X, y = make_sequences(scaled, self.lookback, self.horizon)
        split = int(len(X) * 0.85)
        X_tr, X_te = X[:split], X[split:]
        y_tr, y_te = y[:split], y[split:]

        self.model = self._build_model(len(FEATURES))
        self.model.fit(
            X_tr, y_tr,
            validation_data=(X_te, y_te),
            epochs=epochs,
            batch_size=64,
            callbacks=[
                __import__("tensorflow").keras.callbacks.EarlyStopping(
                    patience=10, restore_best_weights=True)
            ],
            verbose=0,
        )
        self.model.save(str(self.model_dir / "lstm_model.keras"))
        self._trained = True

        preds_sc = self.model.predict(X_te, verbose=0)
        mae_vals = {}
        for i, t in enumerate(TARGETS):
            p = preds_sc[:, :, i].ravel()
            a = y_te[:, :, i].ravel()
            mae_vals[t] = round(float(np.mean(np.abs(p - a))), 4)
        log.info("LSTM trained", mae=mae_vals, epochs=epochs)
        return mae_vals

    def load(self) -> bool:
        try:
            import tensorflow as tf
            mp = self.model_dir / "lstm_model.keras"
            sp = self.model_dir / "lstm_scaler.pkl"
            if mp.exists() and sp.exists():
                self.model   = tf.keras.models.load_model(str(mp))
                self.scaler  = joblib.load(sp)
                self._trained = True
                return True
        except Exception as e:
            log.warning("LSTM load failed", error=str(e))
        return False

    def predict_point(self, history_df: pd.DataFrame) -> pd.DataFrame:
        if not self._trained:
            raise RuntimeError("LSTM not trained.")

        df = history_df.sort_values("date").reset_index(drop=True)
        df = add_calendar_features(df)
        df = df[["date"] + FEATURES].dropna()

        if len(df) < self.lookback:
            raise ValueError(f"Need at least {self.lookback} days of history.")

        window = df[FEATURES].values[-self.lookback:]
        scaled = self.scaler.transform(window)
        X      = scaled[np.newaxis, :, :]

        pred_sc = self.model.predict(X, verbose=0)[0]   # (horizon, 3)

        # Inverse-transform only the 3 target columns
        dummy      = np.zeros((self.horizon, len(FEATURES)))
        dummy[:, :3] = pred_sc
        inv        = self.scaler.inverse_transform(dummy)
        pred_vals  = inv[:, :3]

        last_date = df["date"].max()
        future_dates = pd.date_range(last_date + pd.Timedelta(days=1),
                                     periods=self.horizon, freq="D")
        records = []
        for i, fd in enumerate(future_dates):
            records.append({
                "date":     fd,
                "rainfall": max(0.0, round(float(pred_vals[i, 0]), 3)),
                "max_temp": round(float(pred_vals[i, 1]), 3),
                "min_temp": round(float(pred_vals[i, 2]), 3),
            })
        return pd.DataFrame(records)


lstm_forecaster = LSTMForecaster()

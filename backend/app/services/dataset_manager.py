"""
Dataset Manager Service
Loads and validates climate data from PostgreSQL.
Provides database-driven access for downstream services.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, Union
import structlog
from sqlalchemy import create_engine

log = structlog.get_logger("dataset_manager")


class DatasetManager:
    def __init__(self, db_url: Optional[str] = None):
        if db_url is None:
            from app.core.config import get_settings
            db_url = get_settings().DATABASE_SYNC_URL
            
        self.db_url = db_url
        self.engine = create_engine(self.db_url)
        self._df: Optional[pd.DataFrame] = None
        self._meta: Optional[dict] = None

    def load(self) -> None:
        # Mask password in URL for safe logging
        masked_url = self.db_url
        try:
            from urllib.parse import urlparse
            p = urlparse(self.db_url)
            if p.password:
                masked_url = self.db_url.replace(p.password, "****")
        except Exception:
            pass
            
        log.info("Connecting to PostgreSQL database", url=masked_url)
        try:
            # Test connection
            with self.engine.connect() as conn:
                pass
            log.info("Database connection verified")
        except Exception as e:
            log.error("Failed to connect to database", error=str(e))
            raise

    @property
    def df(self) -> pd.DataFrame:
        if self._df is None:
            log.warning("Loading entire climate_records table into memory. This is slow and memory-intensive!")
            self._df = pd.read_sql(
                "SELECT date, latitude, longitude, rainfall, max_temp, min_temp FROM climate_records", 
                self.engine
            )
            self._df["date"] = pd.to_datetime(self._df["date"])
            self._df["latitude"]  = self._df["latitude"].astype(np.float32)
            self._df["longitude"] = self._df["longitude"].astype(np.float32)
            self._df["rainfall"]  = self._df["rainfall"].astype(np.float32)
            self._df["max_temp"]  = self._df["max_temp"].astype(np.float32)
            self._df["min_temp"]  = self._df["min_temp"].astype(np.float32)
        return self._df

    def get_quality_report(self) -> dict:
        try:
            # 1. Fetch counts and missing values
            query_stats = """
                SELECT
                    COUNT(*) as total_rows,
                    SUM(CASE WHEN rainfall IS NULL THEN 1 ELSE 0 END) as missing_rainfall,
                    SUM(CASE WHEN max_temp IS NULL THEN 1 ELSE 0 END) as missing_max_temp,
                    SUM(CASE WHEN min_temp IS NULL THEN 1 ELSE 0 END) as missing_min_temp,
                    COUNT(CASE WHEN rainfall IS NOT NULL AND max_temp IS NOT NULL AND min_temp IS NOT NULL THEN 1 END) as valid_rows
                FROM climate_records
            """
            stats_df = pd.read_sql(query_stats, self.engine)
            if stats_df.empty:
                return {}
            
            row = stats_df.iloc[0]
            total = int(row["total_rows"])
            valid = int(row["valid_rows"])
            missing_rf = int(row["missing_rainfall"] or 0)
            missing_tx = int(row["missing_max_temp"] or 0)
            missing_tn = int(row["missing_min_temp"] or 0)

            # 2. Date gaps
            query_dates = "SELECT DISTINCT date FROM climate_records ORDER BY date"
            dates_df = pd.read_sql(query_dates, self.engine)
            gaps = []
            if not dates_df.empty:
                dates_df["date"] = pd.to_datetime(dates_df["date"])
                min_date = dates_df["date"].min()
                max_date = dates_df["date"].max()
                all_dates = pd.date_range(min_date, max_date, freq="D")
                actual = set(dates_df["date"].dt.date.unique())
                gaps = [str(d.date()) for d in all_dates if d.date() not in actual]

            # 3. Outliers (using percentile_cont in SQL)
            query_percentiles = """
                SELECT
                    percentile_cont(0.01) WITHIN GROUP (ORDER BY rainfall) as rf_q1,
                    percentile_cont(0.99) WITHIN GROUP (ORDER BY rainfall) as rf_q3,
                    percentile_cont(0.01) WITHIN GROUP (ORDER BY max_temp) as tx_q1,
                    percentile_cont(0.99) WITHIN GROUP (ORDER BY max_temp) as tx_q3,
                    percentile_cont(0.01) WITHIN GROUP (ORDER BY min_temp) as tn_q1,
                    percentile_cont(0.99) WITHIN GROUP (ORDER BY min_temp) as tn_q3
                FROM climate_records
            """
            pct_df = pd.read_sql(query_percentiles, self.engine)
            outliers = 0
            if not pct_df.empty:
                p_row = pct_df.iloc[0]
                rf_q1 = float(p_row["rf_q1"] or 0)
                rf_q3 = float(p_row["rf_q3"] or 0)
                tx_q1 = float(p_row["tx_q1"] or 0)
                tx_q3 = float(p_row["tx_q3"] or 0)
                tn_q1 = float(p_row["tn_q1"] or 0)
                tn_q3 = float(p_row["tn_q3"] or 0)
                
                rf_iqr = rf_q3 - rf_q1
                tx_iqr = tx_q3 - tx_q1
                tn_iqr = tn_q3 - tn_q1

                query_outliers = """
                    SELECT COUNT(*) as outlier_count
                    FROM climate_records
                    WHERE
                        (rainfall < %(rf_min)s OR rainfall > %(rf_max)s) OR
                        (max_temp < %(tx_min)s OR max_temp > %(tx_max)s) OR
                        (min_temp < %(tn_min)s OR min_temp > %(tn_max)s)
                """
                params = {
                    "rf_min": rf_q1 - 3*rf_iqr, "rf_max": rf_q3 + 3*rf_iqr,
                    "tx_min": tx_q1 - 3*tx_iqr, "tx_max": tx_q3 + 3*tx_iqr,
                    "tn_min": tn_q1 - 3*tn_iqr, "tn_max": tn_q3 + 3*tn_iqr
                }
                outliers_df = pd.read_sql(query_outliers, self.engine, params=params)
                if not outliers_df.empty:
                    outliers = int(outliers_df.iloc[0]["outlier_count"])

            return {
                "total_rows": total,
                "missing_rainfall": missing_rf,
                "missing_max_temp": missing_tx,
                "missing_min_temp": missing_tn,
                "completeness_pct": round(100 * valid / total, 2) if total > 0 else 0.0,
                "outlier_count": outliers,
                "date_gaps": gaps,
            }
        except Exception as e:
            log.error("Failed to compute quality report", error=str(e))
            return {
                "total_rows": 0,
                "error": str(e)
            }

    def get_meta(self) -> dict:
        if self._meta is not None:
            return self._meta

        log.info("Fetching dataset metadata from PostgreSQL")
        query = """
            SELECT
                COUNT(*) as total_rows,
                MIN(date) as date_start,
                MAX(date) as date_end,
                MIN(latitude) as lat_min,
                MAX(latitude) as lat_max,
                MIN(longitude) as lon_min,
                MAX(longitude) as lon_max,
                COUNT(DISTINCT latitude) as unique_lats,
                COUNT(DISTINCT longitude) as unique_lons,
                COUNT(DISTINCT date) as unique_dates
            FROM climate_records
        """
        try:
            df_meta = pd.read_sql(query, self.engine)
            if df_meta.empty or df_meta.iloc[0]["total_rows"] == 0:
                return {
                    "name": "IMD India 2025 (Empty)",
                    "total_rows": 0,
                    "status": "empty"
                }

            row = df_meta.iloc[0]
            self._meta = {
                "name": "IMD India 2025",
                "total_rows": int(row["total_rows"]),
                "date_start": str(row["date_start"]),
                "date_end": str(row["date_end"]),
                "lat_min": float(row["lat_min"]),
                "lat_max": float(row["lat_max"]),
                "lon_min": float(row["lon_min"]),
                "lon_max": float(row["lon_max"]),
                "unique_lats": int(row["unique_lats"]),
                "unique_lons": int(row["unique_lons"]),
                "unique_dates": int(row["unique_dates"]),
                "status": "loaded",
            }
            return self._meta
        except Exception as e:
            log.error("Failed to fetch metadata", error=str(e))
            return {
                "name": "IMD India 2025",
                "total_rows": 0,
                "status": "error",
                "error": str(e)
            }

    def get_grid_for_date(self, date_str: str, variable: str,
                          bbox: Optional[list] = None) -> pd.DataFrame:
        # Sanitize variable to prevent SQL injection
        allowed_vars = ["rainfall", "max_temp", "min_temp"]
        if variable not in allowed_vars:
            raise ValueError(f"Invalid variable: {variable}")

        query = f"SELECT latitude, longitude, {variable} FROM climate_records WHERE date = %(date)s"
        params = {"date": date_str}
        if bbox:
            lon_min, lat_min, lon_max, lat_max = bbox
            query += " AND longitude >= %(lon_min)s AND longitude <= %(lon_max)s AND latitude >= %(lat_min)s AND latitude <= %(lat_max)s"
            params.update({
                "lon_min": lon_min,
                "lon_max": lon_max,
                "lat_min": lat_min,
                "lat_max": lat_max
            })
        
        df = pd.read_sql(query, self.engine, params=params)
        df["latitude"]  = df["latitude"].astype(np.float32)
        df["longitude"] = df["longitude"].astype(np.float32)
        if variable in df.columns:
            df[variable] = df[variable].astype(np.float32)
        return df.dropna(subset=[variable])

    def get_timeseries(self, lat: float, lon: float,
                       start: str, end: str) -> pd.DataFrame:
        tol = 0.15
        query = """
            SELECT date, latitude, longitude, rainfall, max_temp, min_temp
            FROM climate_records
            WHERE latitude >= %(lat_min)s AND latitude <= %(lat_max)s
              AND longitude >= %(lon_min)s AND longitude <= %(lon_max)s
              AND date >= %(start)s AND date <= %(end)s
            ORDER BY date
        """
        params = {
            "lat_min": lat - tol,
            "lat_max": lat + tol,
            "lon_min": lon - tol,
            "lon_max": lon + tol,
            "start": start,
            "end": end
        }
        df = pd.read_sql(query, self.engine, params=params)
        df["date"] = pd.to_datetime(df["date"])
        df["latitude"]  = df["latitude"].astype(np.float32)
        df["longitude"] = df["longitude"].astype(np.float32)
        df["rainfall"]  = df["rainfall"].astype(np.float32)
        df["max_temp"]  = df["max_temp"].astype(np.float32)
        df["min_temp"]  = df["min_temp"].astype(np.float32)
        return df.reset_index(drop=True)

    def get_unique_locations(self, limit: int = 200) -> pd.DataFrame:
        query = "SELECT DISTINCT latitude, longitude FROM climate_records LIMIT %(limit)s"
        df = pd.read_sql(query, self.engine, params={"limit": limit})
        df["latitude"]  = df["latitude"].astype(np.float32)
        df["longitude"] = df["longitude"].astype(np.float32)
        return df

    def get_national_daily_averages(self) -> pd.DataFrame:
        query = """
            SELECT date,
                   AVG(rainfall) as rainfall,
                   AVG(max_temp) as max_temp,
                   AVG(min_temp) as min_temp
            FROM climate_records
            GROUP BY date
            ORDER BY date
        """
        df = pd.read_sql(query, self.engine)
        df["date"] = pd.to_datetime(df["date"])
        df["rainfall"]  = df["rainfall"].astype(np.float32)
        df["max_temp"]  = df["max_temp"].astype(np.float32)
        df["min_temp"]  = df["min_temp"].astype(np.float32)
        return df

    def get_national_daily_averages_for_range(self, start: str, end: str) -> pd.DataFrame:
        query = """
            SELECT date,
                   AVG(rainfall) as rainfall,
                   AVG(max_temp) as max_temp,
                   AVG(min_temp) as min_temp
            FROM climate_records
            WHERE date >= %(start)s AND date <= %(end)s
            GROUP BY date
            ORDER BY date
        """
        df = pd.read_sql(query, self.engine, params={"start": start, "end": end})
        df["date"] = pd.to_datetime(df["date"])
        df["rainfall"]  = df["rainfall"].astype(np.float32)
        df["max_temp"]  = df["max_temp"].astype(np.float32)
        df["min_temp"]  = df["min_temp"].astype(np.float32)
        return df

    def get_data_for_range(self, start: str, end: str, bbox: Optional[list] = None) -> pd.DataFrame:
        query = """
            SELECT date, latitude, longitude, rainfall, max_temp, min_temp
            FROM climate_records
            WHERE date >= %(start)s AND date <= %(end)s
        """
        params = {"start": start, "end": end}
        if bbox:
            lon_min, lat_min, lon_max, lat_max = bbox
            query += " AND longitude >= %(lon_min)s AND longitude <= %(lon_max)s AND latitude >= %(lat_min)s AND latitude <= %(lat_max)s"
            params.update({
                "lon_min": lon_min,
                "lon_max": lon_max,
                "lat_min": lat_min,
                "lat_max": lat_max
            })
        df = pd.read_sql(query, self.engine, params=params)
        df["date"] = pd.to_datetime(df["date"])
        df["latitude"]  = df["latitude"].astype(np.float32)
        df["longitude"] = df["longitude"].astype(np.float32)
        df["rainfall"]  = df["rainfall"].astype(np.float32)
        df["max_temp"]  = df["max_temp"].astype(np.float32)
        df["min_temp"]  = df["min_temp"].astype(np.float32)
        return df

    def get_latest_date(self) -> pd.Timestamp:
        query = "SELECT MAX(date) as max_date FROM climate_records"
        df = pd.read_sql(query, self.engine)
        if not df.empty and df.iloc[0]["max_date"] is not None:
            return pd.Timestamp(df.iloc[0]["max_date"])
        return pd.Timestamp("2025-12-31")


_manager: Optional[DatasetManager] = None


def get_dataset_manager() -> DatasetManager:
    global _manager
    if _manager is None:
        from app.core.config import get_settings
        settings = get_settings()
        _manager = DatasetManager(settings.DATABASE_SYNC_URL)
        _manager.load()
    return _manager

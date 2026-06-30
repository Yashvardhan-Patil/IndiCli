"""
Data Harmonization Engine
Handles spatial alignment, temporal alignment, and missing value imputation.
"""

import pandas as pd
import numpy as np
from scipy.interpolate import griddata
from typing import Optional
import structlog

log = structlog.get_logger("harmonization")


class HarmonizationEngine:

    # ── Temporal Alignment ────────────────────────────────────────────────────

    @staticmethod
    def fill_temporal_gaps(df: pd.DataFrame, variable: str,
                           method: str = "linear") -> pd.DataFrame:
        """Fill temporal gaps at each grid point using interpolation."""
        result = []
        for (lat, lon), grp in df.groupby(["latitude", "longitude"]):
            grp = grp.set_index("date").sort_index()
            grp[variable] = grp[variable].interpolate(method=method, limit=7)
            grp = grp.reset_index()
            grp["latitude"]  = lat
            grp["longitude"] = lon
            result.append(grp)
        return pd.concat(result, ignore_index=True)

    # ── Spatial Alignment ─────────────────────────────────────────────────────

    @staticmethod
    def regrid_to_target(source_df: pd.DataFrame, variable: str,
                          target_lats: np.ndarray,
                          target_lons: np.ndarray,
                          date_col: str = "date") -> pd.DataFrame:
        """Bilinear regridding using scipy griddata for a single variable."""
        records = []
        lat_grid, lon_grid = np.meshgrid(target_lats, target_lons, indexing="ij")
        target_pts = np.column_stack([lat_grid.ravel(), lon_grid.ravel()])

        for date_val, grp in source_df.groupby(date_col):
            valid = grp.dropna(subset=[variable])
            if len(valid) < 4:
                continue
            pts  = valid[["latitude", "longitude"]].values
            vals = valid[variable].values
            interpolated = griddata(pts, vals, target_pts, method="linear")
            for i, (la, lo) in enumerate(target_pts):
                records.append({
                    "date": date_val, "latitude": la, "longitude": lo,
                    variable: float(interpolated[i]) if not np.isnan(interpolated[i]) else None,
                })
        return pd.DataFrame(records)

    # ── Missing Value Imputation ──────────────────────────────────────────────

    @staticmethod
    def impute_spatial(df: pd.DataFrame, variable: str,
                       date_col: str = "date") -> pd.DataFrame:
        """Fill NaN values using IDW from neighboring grid points on same day."""
        df = df.copy()
        for date_val, grp_idx in df.groupby(date_col).groups.items():
            grp   = df.loc[grp_idx]
            valid = grp.dropna(subset=[variable])
            nan_mask = grp[variable].isna()
            if nan_mask.sum() == 0 or len(valid) == 0:
                continue
            for idx in grp[nan_mask].index:
                lat0, lon0 = df.at[idx, "latitude"], df.at[idx, "longitude"]
                dists = np.sqrt(
                    (valid["latitude"] - lat0)**2 +
                    (valid["longitude"] - lon0)**2
                )
                closest = valid.loc[dists.nsmallest(4).index]
                d = dists[closest.index].values
                w = 1.0 / (d + 1e-6)
                df.at[idx, variable] = float(
                    np.average(closest[variable].values, weights=w)
                )
        return df

    # ── Composite Pipeline ────────────────────────────────────────────────────

    def harmonize(self, df: pd.DataFrame,
                  variables: list = None) -> pd.DataFrame:
        variables = variables or ["rainfall", "max_temp", "min_temp"]
        log.info("Starting harmonization", rows=len(df), variables=variables)

        for var in variables:
            if var not in df.columns:
                continue
            missing_before = df[var].isna().sum()
            df = self.impute_spatial(df, var)
            df = self.fill_temporal_gaps(df, var)
            missing_after = df[var].isna().sum()
            log.info("Harmonized variable", variable=var,
                     filled=int(missing_before - missing_after))
        return df


harmonization_engine = HarmonizationEngine()

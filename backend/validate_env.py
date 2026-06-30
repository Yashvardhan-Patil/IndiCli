import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.config import get_settings
import os

s = get_settings()

print("=" * 66)
print("  ClimateTwin Bharat — .env Validation Report")
print("=" * 66)

sections = {
    "APPLICATION": [
        ("APP_NAME",  s.APP_NAME),
        ("APP_ENV",   s.APP_ENV),
        ("APP_HOST",  s.APP_HOST),
        ("APP_PORT",  s.APP_PORT),
        ("DEBUG",     s.DEBUG),
    ],
    "DATABASE": [
        ("DATABASE_URL",      s.DATABASE_URL[:50] + "..."),
        ("DATABASE_SYNC_URL", s.DATABASE_SYNC_URL[:50] + "..."),
        ("DB_HOST",    s.DB_HOST),
        ("DB_PORT",    s.DB_PORT),
        ("DB_NAME",    s.DB_NAME),
        ("DB_USER",    s.DB_USER),
        ("DB_PASSWORD","*" * len(s.DB_PASSWORD)),
    ],
    "SECURITY": [
        ("SECRET_KEY",                  s.SECRET_KEY[:12] + "..."),
        ("JWT_ALGORITHM",               s.JWT_ALGORITHM),
        ("ACCESS_TOKEN_EXPIRE_MINUTES", s.ACCESS_TOKEN_EXPIRE_MINUTES),
    ],
    "CORS": [
        ("ALLOWED_ORIGINS", s.ALLOWED_ORIGINS),
        ("origins_list",    s.origins_list),
    ],
    "DATASET PATHS": [
        ("MASTER_CSV_PATH",    s.MASTER_CSV_PATH),
        ("NETCDF_DIR",         s.NETCDF_DIR),
        ("PROCESSED_DATA_DIR", s.PROCESSED_DATA_DIR),
        ("RAW_IMD_DIR",        s.RAW_IMD_DIR),
        ("RAW_INSAT_DIR",      s.RAW_INSAT_DIR),
    ],
    "MODEL PATHS": [
        ("MODELS_DIR",         s.MODELS_DIR),
        ("MODEL_SAVE_DIR",     s.MODEL_SAVE_DIR),
        ("LSTM_MODEL_PATH",    s.LSTM_MODEL_PATH),
        ("XGBOOST_MODEL_PATH", s.XGBOOST_MODEL_PATH),
    ],
    "RUNTIME DIRS": [
        ("UPLOAD_DIR", s.UPLOAD_DIR),
        ("CACHE_DIR",  s.CACHE_DIR),
        ("LOG_DIR",    s.LOG_DIR),
    ],
    "FORECASTING": [
        ("FORECAST_HORIZON_DAYS",    s.FORECAST_HORIZON_DAYS),
        ("LSTM_LOOKBACK_DAYS",       s.LSTM_LOOKBACK_DAYS),
        ("XGBOOST_N_ESTIMATORS",     s.XGBOOST_N_ESTIMATORS),
        ("ENSEMBLE_WEIGHTS_XGBOOST", s.ENSEMBLE_WEIGHTS_XGBOOST),
        ("ENSEMBLE_WEIGHTS_LSTM",    s.ENSEMBLE_WEIGHTS_LSTM),
        ("ensemble_sum",             round(s.ENSEMBLE_WEIGHTS_XGBOOST + s.ENSEMBLE_WEIGHTS_LSTM, 4)),
    ],
    "LOGGING": [
        ("LOG_LEVEL", s.LOG_LEVEL),
    ],
}

issues = []

for section, fields in sections.items():
    print(f"\n  [{section}]")
    for key, val in fields:
        # Path existence check
        status = ""
        if "PATH" in key or "DIR" in key:
            import pathlib
            p = pathlib.Path(str(val))
            if p.exists():
                status = "  OK"
            elif key == "MASTER_CSV_PATH":
                status = "  OPTIONAL (only needed for ingestion)"
            else:
                status = "  MISSING (will be created at runtime)"
                issues.append(f"{key}: {val}")
        elif key == "ensemble_sum":
            status = "  OK" if abs(float(val) - 1.0) < 0.001 else "  WARN: weights do not sum to 1.0"
        print(f"    {key:<32s} = {val}{status}")

print()
if issues:
    print(f"  NOTICE: {len(issues)} path(s) not yet on disk (expected before first run):")
    for i in issues:
        print(f"    - {i}")
else:
    print("  All paths validated.")

print()
print("  Dataset check:")
import pathlib
csv = pathlib.Path(s.MASTER_CSV_PATH)
print(f"    MASTER_CSV exists: {csv.exists()}")
if csv.exists():
    import os
    size_mb = os.path.getsize(csv) / 1024 / 1024
    print(f"    File size: {size_mb:.1f} MB")

print()
print("=" * 66)
print("  .env validation complete — config.py loaded successfully")
print("=" * 66)

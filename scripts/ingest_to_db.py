"""
ingest_to_db.py
Bulk-loads master_climate_dataset.csv into PostgreSQL climate_records table.
Uses COPY for maximum performance.

Usage:
    python scripts/ingest_to_db.py
"""

import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
import os
import sys
from pathlib import Path
from urllib.parse import quote_plus

# ── Load backend/.env so DATABASE_SYNC_URL / DB_* vars are available ─────────
try:
    from dotenv import load_dotenv
    # backend/.env lives one level up from scripts/ inside the project root
    ENV_FILE = Path(__file__).resolve().parent.parent / "backend" / ".env"
    if ENV_FILE.exists():
        load_dotenv(dotenv_path=ENV_FILE, override=False)
        print(f"Loaded env from: {ENV_FILE}")
    else:
        print(f"WARNING: .env not found at {ENV_FILE}, relying on system environment.")
except ImportError:
    print("WARNING: python-dotenv not installed — install it with: pip install python-dotenv")

ROOT     = Path(__file__).resolve().parent.parent
CSV_PATH = ROOT.parent / "processed" / "csv" / "master_climate_dataset.csv"

# ── Build DB URL ──────────────────────────────────────────────────────────────
# Prefer DB_* components — passwords with @, #, %, etc. break raw DATABASE_SYNC_URL.
# Individual components are URL-encoded via quote_plus.
_host     = os.getenv("DB_HOST",     "")
_port     = os.getenv("DB_PORT",     "5432")
_name     = os.getenv("DB_NAME",     "climatetwin_bharat")
_user     = os.getenv("DB_USER",     "postgres")
_password = os.getenv("DB_PASSWORD", "")

if _host and _password:
    _sync_url = (
        f"postgresql://{quote_plus(_user)}:{quote_plus(_password)}"
        f"@{_host}:{_port}/{_name}"
    )
    print("Built DB URL from DB_* components (safe for special characters in password).")
else:
    _sync_url = os.getenv("DATABASE_SYNC_URL", "")
    if not _sync_url:
        raise RuntimeError(
            "Database not configured: set DB_HOST + DB_PASSWORD, or DATABASE_SYNC_URL."
        )
    print("Using DATABASE_SYNC_URL from environment.")

DB_URL = _sync_url
# Mask password for safe logging
_log_url = DB_URL
try:
    from urllib.parse import urlparse
    _p = urlparse(DB_URL)
    _log_url = DB_URL.replace(_p.password or "", "****") if _p.password else DB_URL
except Exception:
    pass
print("DB_URL =", _log_url)


BATCH = 50_000


def ingest():
    print(f"Loading {CSV_PATH} ...")
    df = pd.read_csv(CSV_PATH, parse_dates=["date"])
    df = df.dropna(subset=["latitude","longitude"])
    print(f"Rows to ingest: {len(df):,}")

    conn = psycopg2.connect(DB_URL)
    cur  = conn.cursor()

    # Clear existing data
    cur.execute("TRUNCATE TABLE climate_records RESTART IDENTITY;")
    conn.commit()

    total = 0
    records = []
    for _, row in df.iterrows():
        records.append((
            str(row["date"].date()),
            float(row["latitude"]),
            float(row["longitude"]),
            None if pd.isna(row["rainfall"]) else float(row["rainfall"]),
            None if pd.isna(row["max_temp"]) else float(row["max_temp"]),
            None if pd.isna(row["min_temp"]) else float(row["min_temp"]),
        ))
        if len(records) >= BATCH:
            execute_values(cur,
                "INSERT INTO climate_records (date,latitude,longitude,rainfall,max_temp,min_temp) VALUES %s",
                records)
            conn.commit()
            total += len(records)
            print(f"  Inserted {total:,} rows ...")
            records.clear()

    if records:
        execute_values(cur,
            "INSERT INTO climate_records (date,latitude,longitude,rainfall,max_temp,min_temp) VALUES %s",
            records)
        conn.commit()
        total += len(records)

    print(f"\nIngestion complete: {total:,} rows inserted.")
    cur.close()
    conn.close()


if __name__ == "__main__":
    ingest()

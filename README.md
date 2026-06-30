# IndiCli

AI-powered Digital Twin of India's Climate System.

## Architecture

```
Dataset (IMD 2025 GRD files)
        |
   Harmonization Engine
        |
   Hybrid Forecasting Engine
   (XGBoost 55% + LSTM 45%)
        |
   Digital Twin Core Engine
        |
   What-If Simulation Engine
        |
   Climate Analytics Engine
        |
   FastAPI REST API
        |
   React + CesiumJS Dashboard
```

## Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 15+ with PostGIS extension
- (Optional) Cesium Ion account for terrain rendering

---

## Quick Start

### 1. Backend Setup

```bash
cd IndiCli/backend

# Create virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Edit .env — update DATABASE_URL and MASTER_CSV_PATH
copy .env.example .env         # then edit

# Start the API server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API docs available at: http://localhost:8000/docs

### 2. Database Setup (Optional — needed for persistence)

```bash
# Run as postgres superuser
psql -U postgres -f ../database/schema.sql

# Load IMD data into PostgreSQL
python ../scripts/ingest_to_db.py
```

### 3. Frontend Setup

```bash
cd IndiCli/frontend

# Edit .env — add your Cesium Ion token
# VITE_CESIUM_TOKEN=your_token_here
# VITE_API_BASE_URL=http://localhost:8000

npm install
npm run dev
```

Frontend runs at: http://localhost:5173

---

## Environment Variables

### Backend (`backend/.env`)

| Variable | Description |
|---|---|
| DATABASE_URL | PostgreSQL async connection string |
| DATABASE_SYNC_URL | PostgreSQL sync connection string (for ingestion) |
| MASTER_CSV_PATH | Path to master_climate_dataset.csv or master_climate_dataset.csv.gz |
| FORECAST_HORIZON_DAYS | Default forecast horizon (default: 30) |
| LSTM_LOOKBACK_DAYS | LSTM sequence lookback window (default: 60) |
| ENSEMBLE_WEIGHTS_XGBOOST | XGBoost ensemble weight (default: 0.55) |
| ENSEMBLE_WEIGHTS_LSTM | LSTM ensemble weight (default: 0.45) |

### Frontend (`frontend/.env`)

| Variable | Description |
|---|---|
| VITE_API_BASE_URL | FastAPI backend URL |
| VITE_CESIUM_TOKEN | Cesium Ion access token (https://cesium.com/ion) |

---

## Render Deployment

This repo includes a starter `render.yaml` plus environment examples:

- `backend/.env.render.example`
- `frontend/.env.render.example`

Before deploying, replace placeholder Render URLs:

- Backend `ALLOWED_ORIGINS` must be your deployed frontend URL.
- Frontend `VITE_API_BASE_URL` must be your deployed backend URL.
- Frontend `VITE_CESIUM_TOKEN` must be set before the frontend build.

Important data/model notes:

- The local Windows path in `backend/.env` is only for development and is ignored by git.
- On Render, set `MASTER_CSV_PATH=./data/master_climate_dataset.csv.gz`.
- Put `master_climate_dataset.csv.gz` in `backend/data/`, mount a Render disk there, or download it from object storage during deployment.
- Keep the trained model files in `backend/models/` so Render does not need to train models on first request.
- Render provides `PORT`; the backend start command in `render.yaml` uses `$PORT`.

Render free instances may sleep, so the first API request can be slow. Forecast and simulation endpoints are also heavier than normal API calls.

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| GET | /datasets/meta | Dataset metadata |
| GET | /datasets/quality | Data quality report |
| GET | /climate-state/current | Grid data for a date+variable |
| GET | /climate-state/timeseries | Location time series |
| GET | /climate-state/national-summary | National climate summary |
| POST | /forecast/point | Point forecast (lat/lon) |
| POST | /forecast/train | Trigger model training |
| POST | /scenario/run | Run what-if simulation |
| GET | /scenario/types | List scenario types |
| POST | /analytics/trend | Trend analysis |
| POST | /analytics/anomaly | Anomaly detection |
| POST | /analytics/risk | Risk assessment |
| GET | /analytics/indicators | Climate indicators |
| GET | /health | Health check |

---

## Scenario Types

| ID | Description |
|---|---|
| temp_plus_1c | +1°C uniform temperature increase |
| temp_plus_2c | +2°C uniform temperature increase |
| rain_plus_20pct | +20% rainfall increase |
| rain_minus_20pct | -20% rainfall reduction |
| drought | -70% rainfall, +1.5°C temperature |
| heatwave | +5°C max temp, -50% rainfall |
| extreme_rainfall | +200% rainfall, -1°C temperature |

---

## Project Structure

```
IndiCli/
├── backend/
│   ├── app/
│   │   ├── api/routes/         # FastAPI routers
│   │   ├── core/               # Config + logging
│   │   ├── db/                 # SQLAlchemy engine
│   │   ├── models/             # ORM + Pydantic schemas
│   │   └── services/
│   │       ├── dataset_manager.py
│   │       ├── digital_twin.py
│   │       ├── forecasting/    # XGBoost, LSTM, Ensemble
│   │       ├── simulation/     # What-If engine
│   │       ├── analytics/      # Trend, Anomaly, Risk
│   │       └── harmonization/  # Spatial/temporal alignment
│   ├── .env
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api/client.js       # Axios API client
│   │   ├── components/
│   │   │   ├── map/            # CesiumGlobe
│   │   │   ├── charts/         # Recharts components
│   │   │   └── ui/             # Reusable UI primitives
│   │   ├── pages/              # Dashboard, Twin, Forecast, Simulation, Analytics, Settings
│   │   ├── store/useStore.js   # Zustand global state
│   │   └── App.jsx
│   ├── .env
│   └── vite.config.js
├── database/
│   └── schema.sql              # PostgreSQL + PostGIS schema
└── scripts/
    └── ingest_to_db.py         # Bulk CSV loader
```

---

## Training AI Models

Models are trained on first forecast request (auto-training).
To pre-train manually:

```bash
# Via API (background task)
curl -X POST http://localhost:8000/forecast/train
```

Trained models are saved to `backend/models/` as:
- `xgb_rainfall.pkl`
- `xgb_max_temp.pkl`
- `xgb_min_temp.pkl`
- `lstm_model.keras`
- `lstm_scaler.pkl`

---

## Dataset Facts (Verified)

| Dataset | Grid | Resolution | Missing Value |
|---|---|---|---|
| MaxTemp 2025 | 31x31 | 1.0° | 99.9 |
| MinTemp 2025 | 31x31 | 1.0° | 99.9 |
| Rainfall 2025 | 129x135 | 0.25° | -999.0 |
| Master CSV | 117x129 | 0.25° | NaN |

- Total rows: 2,106,050
- Date range: 2025-01-01 to 2025-12-31
- Lat range: 8.25° to 37.25°N
- Lon range: 68.0° to 100.0°E

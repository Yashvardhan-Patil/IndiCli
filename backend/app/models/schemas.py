from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import date, datetime
from enum import Enum


# ── Enums ─────────────────────────────────────────────────────────────────────

class ScenarioType(str, Enum):
    TEMP_PLUS_1    = "temp_plus_1c"
    TEMP_PLUS_2    = "temp_plus_2c"
    RAIN_PLUS_20   = "rain_plus_20pct"
    RAIN_MINUS_20  = "rain_minus_20pct"
    DROUGHT        = "drought"
    HEATWAVE       = "heatwave"
    EXTREME_RAIN   = "extreme_rainfall"

class ModelType(str, Enum):
    XGBOOST  = "xgboost"
    LSTM     = "lstm"
    ENSEMBLE = "ensemble"

class AnalysisType(str, Enum):
    TREND    = "trend"
    ANOMALY  = "anomaly"
    RISK     = "risk"
    INDICATORS = "indicators"


# ── Dataset Schemas ───────────────────────────────────────────────────────────

class DatasetInfo(BaseModel):
    name: str
    total_rows: int
    date_start: date
    date_end: date
    lat_min: float
    lat_max: float
    lon_min: float
    lon_max: float
    status: str
    metadata: Dict[str, Any] = {}

class DataQualityReport(BaseModel):
    total_rows: int
    missing_rainfall: int
    missing_max_temp: int
    missing_min_temp: int
    completeness_pct: float
    outlier_count: int
    date_gaps: List[str]


# ── Climate State Schemas ─────────────────────────────────────────────────────

class ClimateGridPoint(BaseModel):
    latitude: float
    longitude: float
    rainfall: Optional[float]
    max_temp: Optional[float]
    min_temp: Optional[float]

class ClimateStateResponse(BaseModel):
    state_type: str   # current | forecast | scenario
    date: date
    variable: str
    grid_points: List[ClimateGridPoint]
    stats: Dict[str, float] = {}

class ClimateStateRequest(BaseModel):
    date: date
    variable: str = "rainfall"
    bbox: Optional[List[float]] = None   # [lon_min, lat_min, lon_max, lat_max]


# ── Forecast Schemas ──────────────────────────────────────────────────────────

class ForecastRequest(BaseModel):
    latitude: float = Field(..., ge=6.0, le=40.0)
    longitude: float = Field(..., ge=65.0, le=102.0)
    horizon_days: int = Field(30, ge=1, le=90)
    model: ModelType = ModelType.ENSEMBLE
    variables: List[str] = ["rainfall", "max_temp", "min_temp"]

class ForecastPoint(BaseModel):
    target_date: date
    rainfall_pred: Optional[float]
    max_temp_pred: Optional[float]
    min_temp_pred: Optional[float]
    confidence: float

class ForecastResponse(BaseModel):
    latitude: float
    longitude: float
    model: str
    forecast_generated_at: datetime
    horizon_days: int
    forecasts: List[ForecastPoint]

class GridForecastRequest(BaseModel):
    date: date
    variable: str = "rainfall"
    model: ModelType = ModelType.ENSEMBLE
    horizon_days: int = 7


# ── Scenario Schemas ──────────────────────────────────────────────────────────

class ScenarioRequest(BaseModel):
    scenario_type: ScenarioType
    base_date: date
    duration_days: int = Field(30, ge=1, le=365)
    bbox: Optional[List[float]] = None

class ScenarioGridPoint(BaseModel):
    latitude: float
    longitude: float
    rainfall: Optional[float]
    max_temp: Optional[float]
    min_temp: Optional[float]
    delta_rainfall: Optional[float]
    delta_max_temp: Optional[float]
    delta_min_temp: Optional[float]

class ScenarioResponse(BaseModel):
    scenario_id: str
    scenario_type: str
    base_date: date
    duration_days: int
    description: str
    grid_points: List[ScenarioGridPoint]
    summary_stats: Dict[str, Any] = {}


# ── Analytics Schemas ─────────────────────────────────────────────────────────

class AnalyticsRequest(BaseModel):
    analysis_type: AnalysisType
    variable: str = "rainfall"
    start_date: date
    end_date: date
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    bbox: Optional[List[float]] = None

class TrendResult(BaseModel):
    dates: List[str]
    values: List[Optional[float]]
    trend_slope: float
    trend_r2: float
    moving_avg_30d: List[Optional[float]]

class AnomalyResult(BaseModel):
    dates: List[str]
    values: List[Optional[float]]
    anomaly_scores: List[float]
    anomaly_flags: List[bool]
    threshold: float

class RiskResult(BaseModel):
    drought_risk: float
    flood_risk: float
    heatwave_risk: float
    cold_wave_risk: float
    composite_risk: float
    risk_level: str

class AnalyticsResponse(BaseModel):
    analysis_type: str
    variable: str
    start_date: date
    end_date: date
    result: Dict[str, Any]

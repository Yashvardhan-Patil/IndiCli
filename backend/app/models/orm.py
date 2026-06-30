from sqlalchemy import (
    Column, Integer, Float, String, Date, DateTime,
    Text, JSON, ForeignKey, Index, func
)
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry
from datetime import datetime
from app.db.database import Base


class ClimateRecord(Base):
    """Historical daily climate observations per grid point."""
    __tablename__ = "climate_records"

    id        = Column(Integer, primary_key=True, index=True)
    date      = Column(Date, nullable=False, index=True)
    latitude  = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    rainfall  = Column(Float)
    max_temp  = Column(Float)
    min_temp  = Column(Float)
    geom      = Column(Geometry(geometry_type="POINT", srid=4326))

    __table_args__ = (
        Index("ix_climate_records_date_lat_lon", "date", "latitude", "longitude"),
        Index("ix_climate_records_geom", "geom", postgresql_using="gist"),
    )


class ForecastRecord(Base):
    """AI-generated forecast outputs."""
    __tablename__ = "forecast_records"

    id              = Column(Integer, primary_key=True, index=True)
    forecast_date   = Column(Date, nullable=False, index=True)
    target_date     = Column(Date, nullable=False, index=True)
    latitude        = Column(Float, nullable=False)
    longitude       = Column(Float, nullable=False)
    rainfall_pred   = Column(Float)
    max_temp_pred   = Column(Float)
    min_temp_pred   = Column(Float)
    confidence      = Column(Float)
    model_type      = Column(String(50))   # xgboost | lstm | ensemble
    geom            = Column(Geometry(geometry_type="POINT", srid=4326))

    __table_args__ = (
        Index("ix_forecast_date_target", "forecast_date", "target_date"),
        Index("ix_forecast_geom", "geom", postgresql_using="gist"),
    )


class ScenarioRecord(Base):
    """What-if scenario simulation outputs."""
    __tablename__ = "scenario_records"

    id            = Column(Integer, primary_key=True, index=True)
    scenario_id   = Column(String(100), nullable=False, index=True)
    scenario_type = Column(String(100), nullable=False)
    date          = Column(Date, nullable=False, index=True)
    latitude      = Column(Float, nullable=False)
    longitude     = Column(Float, nullable=False)
    rainfall      = Column(Float)
    max_temp      = Column(Float)
    min_temp      = Column(Float)
    delta_rainfall= Column(Float)
    delta_max_temp= Column(Float)
    delta_min_temp= Column(Float)
    geom          = Column(Geometry(geometry_type="POINT", srid=4326))

    __table_args__ = (
        Index("ix_scenario_id_date", "scenario_id", "date"),
        Index("ix_scenario_geom", "geom", postgresql_using="gist"),
    )


class AnalyticsResult(Base):
    """Stored analytics computation results."""
    __tablename__ = "analytics_results"

    id           = Column(Integer, primary_key=True, index=True)
    analysis_type= Column(String(100), nullable=False, index=True)
    variable     = Column(String(50))
    region       = Column(String(200))
    start_date   = Column(Date)
    end_date     = Column(Date)
    result_json  = Column(JSON)
    created_at   = Column(DateTime, default=datetime.utcnow)


class DatasetMeta(Base):
    """Tracks loaded datasets and ingestion status."""
    __tablename__ = "dataset_meta"

    id           = Column(Integer, primary_key=True, index=True)
    name         = Column(String(200), nullable=False, unique=True)
    source_path  = Column(Text)
    total_rows   = Column(Integer)
    date_start   = Column(Date)
    date_end     = Column(Date)
    lat_min      = Column(Float)
    lat_max      = Column(Float)
    lon_min      = Column(Float)
    lon_max      = Column(Float)
    status       = Column(String(50), default="pending")
    ingested_at  = Column(DateTime, default=datetime.utcnow)
    metadata_json= Column(JSON)

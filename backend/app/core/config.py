from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import model_validator
from functools import lru_cache
from pathlib import Path
from urllib.parse import quote_plus

_BACKEND_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",          # silently ignore unknown keys
    )

    # ── Application ───────────────────────────────────────────────────────────
    APP_NAME: str = "IndiCli"
    APP_ENV:  str = "development"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    DEBUG:    bool = True

    # ── Database ──────────────────────────────────────────────────────────────
    DATABASE_URL:      str = "postgresql+asyncpg://postgres:password@localhost:5432/climatetwin"
    DATABASE_SYNC_URL: str = "postgresql://postgres:password@localhost:5432/climatetwin"
    DB_HOST:     str = "localhost"
    DB_PORT:     int = 5432
    DB_NAME:     str = "climatetwin"
    DB_USER:     str = "postgres"
    DB_PASSWORD: str = "password"

    # ── Security ──────────────────────────────────────────────────────────────
    SECRET_KEY:                  str = "change-me-in-production"
    JWT_ALGORITHM:               str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    # ── CORS ──────────────────────────────────────────────────────────────────
    ALLOWED_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    # ── Dataset Paths ─────────────────────────────────────────────────────────
    MASTER_CSV_PATH:    str = "../../processed/csv/master_climate_dataset.csv"
    NETCDF_DIR:         str = "../../processed/netcdf"
    PROCESSED_DATA_DIR: str = "../../processed"
    RAW_IMD_DIR:        str = "../../Dataset/IMD"
    RAW_INSAT_DIR:      str = "../../Dataset/INSAT"

    # ── Model Paths ───────────────────────────────────────────────────────────
    MODELS_DIR:          str = "./models"
    MODEL_SAVE_DIR:      str = "./models"
    LSTM_MODEL_PATH:     str = "./models/lstm_model.keras"
    XGBOOST_MODEL_PATH:  str = "./models/xgb_rainfall.pkl"

    # ── Runtime Directories ───────────────────────────────────────────────────
    UPLOAD_DIR: str = "./uploads"
    CACHE_DIR:  str = "./cache"
    LOG_DIR:    str = "./logs"

    # ── Forecasting ───────────────────────────────────────────────────────────
    FORECAST_HORIZON_DAYS:    int   = 30
    LSTM_LOOKBACK_DAYS:       int   = 60
    XGBOOST_N_ESTIMATORS:     int   = 200
    ENSEMBLE_WEIGHTS_XGBOOST: float = 0.55
    ENSEMBLE_WEIGHTS_LSTM:    float = 0.45

    # ── Logging ───────────────────────────────────────────────────────────────
    LOG_LEVEL: str = "INFO"

    # ── Computed properties ───────────────────────────────────────────────────
    @property
    def origins_list(self) -> list[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",")]

    @property
    def models_path(self) -> Path:
        p = Path(self.MODELS_DIR)
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def upload_path(self) -> Path:
        p = Path(self.UPLOAD_DIR)
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def cache_path(self) -> Path:
        p = Path(self.CACHE_DIR)
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def log_path(self) -> Path:
        p = Path(self.LOG_DIR)
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"

    @model_validator(mode="after")
    def build_database_urls_from_components(self) -> "Settings":
        """Rebuild DB URLs from DB_* only when component vars are explicitly set."""
        provided = self.model_fields_set
        database_url_set = any(k in provided for k in ("DATABASE_URL", "DATABASE_SYNC_URL"))
        db_components_set = any(k in provided for k in (
            "DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD"
        ))
        if db_components_set and not database_url_set and self.DB_HOST and self.DB_PASSWORD:
            sync = (
                f"postgresql://{quote_plus(self.DB_USER)}:{quote_plus(self.DB_PASSWORD)}"
                f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
            )
            object.__setattr__(self, "DATABASE_SYNC_URL", sync)
            object.__setattr__(
                self,
                "DATABASE_URL",
                sync.replace("postgresql://", "postgresql+asyncpg://", 1),
            )
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import structlog

from app.core.config import get_settings
from app.core.logging import setup_logging
from app.api.routes import datasets, climate_state, forecast, scenario, analytics

settings = get_settings()
setup_logging(settings.DEBUG)
log = structlog.get_logger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("IndiCli backend starting up ...")
    # Verify database connection
    from app.services.dataset_manager import get_dataset_manager
    get_dataset_manager()
    
    # Pre-load/train forecasting models
    from app.services.forecasting.ensemble import ensemble_forecaster
    try:
        ensemble_forecaster._ensure_trained()
    except Exception as e:
        log.warning("Failed to pre-load forecasting models during startup", error=str(e))
        
    log.info("Dataset and models loaded and ready.")
    yield
    log.info("Shutting down ...")


app = FastAPI(
    title="IndiCli API",
    description="AI-powered Digital Twin of India's Climate System",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register all routers
app.include_router(datasets.router)
app.include_router(climate_state.router)
app.include_router(forecast.router)
app.include_router(scenario.router)
app.include_router(analytics.router)


@app.get("/", tags=["Health"])
async def root():
    return {
        "service": "IndiCli API",
        "version": "1.0.0",
        "status":  "operational",
        "docs":    "/docs",
    }


@app.get("/health", tags=["Health"])
async def health():
    from app.services.dataset_manager import get_dataset_manager
    dm = get_dataset_manager()
    meta = dm.get_meta()
    return {
        "status":       "healthy",
        "dataset_rows": meta["total_rows"],
        "date_range":   f"{meta['date_start']} to {meta['date_end']}",
    }

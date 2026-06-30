from fastapi import APIRouter, HTTPException
from app.models.schemas import ScenarioRequest
from app.services.simulation.engine import simulation_engine, SCENARIO_DESCRIPTIONS

router = APIRouter(prefix="/scenario", tags=["Scenarios"])


@router.post("/run")
async def run_scenario(req: ScenarioRequest):
    try:
        result = simulation_engine.run_scenario(
            scenario_type=req.scenario_type.value,
            base_date=str(req.base_date),
            duration_days=req.duration_days,
            bbox=req.bbox,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/types")
async def scenario_types():
    return {
        "scenarios": [
            {"id": k, "description": v}
            for k, v in SCENARIO_DESCRIPTIONS.items()
        ]
    }

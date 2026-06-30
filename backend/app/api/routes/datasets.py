from fastapi import APIRouter, HTTPException
from app.services.dataset_manager import get_dataset_manager

router = APIRouter(prefix="/datasets", tags=["Datasets"])


@router.get("/")
async def list_datasets():
    dm = get_dataset_manager()
    return {"datasets": [dm.get_meta()]}


@router.get("/meta")
async def dataset_meta():
    dm = get_dataset_manager()
    return dm.get_meta()


@router.get("/quality")
async def data_quality():
    dm = get_dataset_manager()
    return dm.get_quality_report()


@router.get("/summary")
async def dataset_summary():
    dm   = get_dataset_manager()
    meta = dm.get_meta()
    qr   = dm.get_quality_report()
    return {"meta": meta, "quality": qr}

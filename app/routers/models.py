from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services import model_service


router = APIRouter(prefix="/api/models", tags=["models"])


class TrainModelRequest(BaseModel):
    model_name: str = "logistic_regression"


@router.post("/train")
def train_model(request: TrainModelRequest):
    try:
        return model_service.train_baseline_model(model_name=request.model_name)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/runs")
def get_model_runs():
    return model_service.list_model_runs()


@router.get("/evaluate")
def evaluate_model():
    latest_run = model_service.get_latest_run()
    if latest_run is None:
        raise HTTPException(status_code=404, detail="No model run exists yet")
    return latest_run

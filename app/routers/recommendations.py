from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services import model_service


router = APIRouter(prefix="/api/recommend", tags=["recommendations"])


class PredictRecommendationRequest(BaseModel):
    limit: int = Field(default=20, gt=0)


@router.post("/predict")
def predict_recommendations(request: PredictRecommendationRequest):
    try:
        return model_service.predict_recommendations(limit=request.limit)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

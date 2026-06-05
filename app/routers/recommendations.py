import csv
from io import StringIO
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Response
from pydantic import BaseModel, Field

from app.services import model_service


router = APIRouter(prefix="/api/recommend", tags=["recommendations"])


class PredictRecommendationRequest(BaseModel):
    limit: int = Field(default=20, gt=0)


CSV_FIELDS = ["customer_id", "probability", "recommend_level", "reason"]


def _resolve_history_run_id(run_id):
    if run_id is not None:
        return run_id
    return model_service.get_latest_recommendation_run_id()


@router.post("/predict")
def predict_recommendations(request: PredictRecommendationRequest):
    try:
        return model_service.predict_recommendations(limit=request.limit)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/history")
def get_recommendation_history(
    run_id: Optional[str] = None,
    limit: int = Query(default=100, gt=0),
):
    effective_run_id = _resolve_history_run_id(run_id)
    if effective_run_id is None:
        return {"run_id": None, "count": 0, "items": []}

    try:
        items = model_service.list_recommendation_history(
            run_id=effective_run_id,
            limit=limit,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "run_id": effective_run_id,
        "count": len(items),
        "items": items,
    }


@router.get("/export")
def export_recommendations(run_id: Optional[str] = None):
    try:
        items = model_service.list_recommendation_history(run_id=run_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=CSV_FIELDS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(items)

    return Response(
        content=output.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": "attachment; filename=recommendations.csv",
        },
    )

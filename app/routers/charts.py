from collections import Counter

from fastapi import APIRouter

from app.services.dataset_service import build_dataset_profile
from app.services import model_service


router = APIRouter(prefix="/api/charts", tags=["charts"])

METRIC_NAMES = ("accuracy", "precision", "recall", "f1", "auc")
RECOMMENDATION_LEVELS = ("high", "medium", "low")


@router.get("/dataset")
def get_dataset_chart():
    profile = build_dataset_profile()
    train_summary = profile["train"]
    positive_count = int(train_summary["positive_count"])
    negative_count = int(train_summary["rows"]) - positive_count

    return {
        "series": [
            {"name": "正样本", "value": positive_count},
            {"name": "负样本", "value": negative_count},
        ]
    }


@router.get("/model-metrics")
def get_model_metrics_chart():
    comparison = model_service.compare_model_runs()
    items = comparison["items"]

    return {
        "models": [item["model_name"] for item in items],
        "metrics": {
            metric_name: [
                float(item["metrics"][metric_name])
                for item in items
            ]
            for metric_name in METRIC_NAMES
        },
    }


@router.get("/recommend-levels")
def get_recommend_level_chart():
    items = model_service.list_recommendation_history(run_id=None, limit=None)
    counts_by_level = Counter(item["recommend_level"] for item in items)

    return {
        "levels": list(RECOMMENDATION_LEVELS),
        "counts": [
            counts_by_level.get(level, 0)
            for level in RECOMMENDATION_LEVELS
        ],
    }

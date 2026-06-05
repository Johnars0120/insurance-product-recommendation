import pandas as pd
import pytest
from fastapi.testclient import TestClient

from app.database import configure_database, create_tables
from app.main import app
import app.services.dataset_service as dataset_service
import app.services.model_service as model_service


@pytest.fixture
def client_with_chart_files(tmp_path, monkeypatch):
    train_data = pd.DataFrame(
        {
            "age": [25, 35, 45, 55, 65, 75],
            "income": [3000, 4500, 5000, 6500, 8000, 9000],
            "claims": [0, 1, 0, 2, 1, 3],
            model_service.TARGET_COLUMN: [0, 1, 0, 1, 0, 1],
        }
    )
    eval_data = pd.DataFrame(
        {
            "age": [28, 48, 68, 78],
            "income": [3200, 5200, 8300, 9100],
            "claims": [0, 1, 1, 3],
            model_service.TARGET_COLUMN: [0, 0, 1, 1],
        }
    )
    train_file = tmp_path / "train.xlsx"
    eval_file = tmp_path / "eval.xlsx"
    train_data.to_excel(train_file, index=False)
    eval_data.to_excel(eval_file, index=False)

    configure_database(f"sqlite:///{(tmp_path / 'chart-history.db').as_posix()}")
    create_tables()
    monkeypatch.setattr(dataset_service, "TRAIN_DATA_FILE", train_file)
    monkeypatch.setattr(dataset_service, "EVAL_DATA_FILE", eval_file)
    monkeypatch.setattr(model_service, "TRAIN_DATA_FILE", train_file)
    monkeypatch.setattr(model_service, "EVAL_DATA_FILE", eval_file)
    monkeypatch.setattr(model_service, "SAVED_MODEL_DIR", tmp_path / "saved_models")
    model_service.reset_latest_run()

    return TestClient(app)


def test_dataset_chart_api_returns_positive_negative_counts(client_with_chart_files):
    response = client_with_chart_files.get("/api/charts/dataset")

    assert response.status_code == 200
    assert response.json() == {
        "series": [
            {"name": "正样本", "value": 3},
            {"name": "负样本", "value": 3},
        ]
    }


def test_model_metrics_chart_api_returns_compare_items(client_with_chart_files):
    train_response = client_with_chart_files.post(
        "/api/models/train", json={"model_name": "logistic_regression"}
    )
    assert train_response.status_code == 200

    response = client_with_chart_files.get("/api/charts/model-metrics")

    assert response.status_code == 200
    body = response.json()
    assert body["models"] == ["logistic_regression"]
    assert body["metrics"]["auc"] == [train_response.json()["metrics"]["auc"]]


def test_model_metrics_chart_api_returns_empty_arrays_without_runs(
    client_with_chart_files,
):
    response = client_with_chart_files.get("/api/charts/model-metrics")

    assert response.status_code == 200
    assert response.json() == {
        "models": [],
        "metrics": {
            "accuracy": [],
            "precision": [],
            "recall": [],
            "f1": [],
            "auc": [],
        },
    }


def test_recommend_level_chart_api_returns_level_counts(client_with_chart_files):
    predict_response = client_with_chart_files.post(
        "/api/recommend/predict", json={"limit": 4}
    )
    assert predict_response.status_code == 200

    response = client_with_chart_files.get("/api/charts/recommend-levels")

    assert response.status_code == 200
    body = response.json()
    assert body["levels"] == ["high", "medium", "low"]
    assert sum(body["counts"]) == 4

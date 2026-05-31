import pandas as pd
import pytest
from fastapi.testclient import TestClient

import app.services.model_service as model_service
from app.main import app


@pytest.fixture
def client_with_model_files(tmp_path, monkeypatch):
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

    monkeypatch.setattr(model_service, "TRAIN_DATA_FILE", train_file)
    monkeypatch.setattr(model_service, "EVAL_DATA_FILE", eval_file)
    monkeypatch.setattr(model_service, "SAVED_MODEL_DIR", tmp_path / "saved_models")
    model_service.reset_latest_run()

    return TestClient(app)


def test_train_api_returns_metrics(client_with_model_files):
    response = client_with_model_files.post(
        "/api/models/train", json={"model_name": "logistic_regression"}
    )

    assert response.status_code == 200
    assert response.json()["metrics"]["auc"] >= 0.0


def test_evaluate_api_returns_latest_metrics_after_training(client_with_model_files):
    client_with_model_files.post(
        "/api/models/train", json={"model_name": "logistic_regression"}
    )

    response = client_with_model_files.get("/api/models/evaluate")

    assert response.status_code == 200
    assert response.json()["model_name"] == "logistic_regression"
    assert "f1" in response.json()["metrics"]


def test_runs_api_returns_latest_run_list(client_with_model_files):
    assert client_with_model_files.get("/api/models/runs").json() == []

    train_response = client_with_model_files.post(
        "/api/models/train", json={"model_name": "logistic_regression"}
    )
    response = client_with_model_files.get("/api/models/runs")

    assert response.status_code == 200
    assert response.json() == [train_response.json()]


def test_evaluate_api_returns_404_before_training(client_with_model_files):
    response = client_with_model_files.get("/api/models/evaluate")

    assert response.status_code == 404
    assert "No model run" in response.json()["detail"]


def test_train_api_rejects_unsupported_model_name(client_with_model_files):
    response = client_with_model_files.post(
        "/api/models/train", json={"model_name": "random_forest"}
    )

    assert response.status_code == 400
    assert "Unsupported model_name" in response.json()["detail"]

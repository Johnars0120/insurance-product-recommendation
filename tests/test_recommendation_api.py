import joblib
import pandas as pd
import pytest
from fastapi.testclient import TestClient

import app.services.model_service as model_service
from app.main import app


class ModelWithoutPredictProba:
    pass


@pytest.fixture
def client_with_recommendation_files(tmp_path, monkeypatch):
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
    saved_model_dir = tmp_path / "saved_models"
    train_data.to_excel(train_file, index=False)
    eval_data.to_excel(eval_file, index=False)

    monkeypatch.setattr(model_service, "TRAIN_DATA_FILE", train_file)
    monkeypatch.setattr(model_service, "EVAL_DATA_FILE", eval_file)
    monkeypatch.setattr(model_service, "SAVED_MODEL_DIR", saved_model_dir)
    model_service.reset_latest_run()

    return {
        "client": TestClient(app),
        "eval_rows": len(eval_data),
        "saved_model_dir": saved_model_dir,
    }


def test_predict_api_trains_if_needed_and_returns_recommendations(
    client_with_recommendation_files,
):
    temp_model_file = client_with_recommendation_files["saved_model_dir"].joinpath(
        "latest_model.joblib"
    )
    assert not temp_model_file.exists()

    response = client_with_recommendation_files["client"].post(
        "/api/recommend/predict", json={"limit": 4}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 4
    assert len(body["items"]) == 4
    first = body["items"][0]
    assert {"customer_id", "probability", "recommend_level", "reason"} <= set(first)
    assert first["customer_id"] == "1"
    assert 0.0 <= first["probability"] <= 1.0
    assert first["recommend_level"] in {"high", "medium", "low"}
    assert temp_model_file.exists()


def test_predict_api_caps_limit_to_available_eval_rows(client_with_recommendation_files):
    response = client_with_recommendation_files["client"].post(
        "/api/recommend/predict", json={"limit": 999}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["count"] == client_with_recommendation_files["eval_rows"]
    assert len(body["items"]) == client_with_recommendation_files["eval_rows"]


def test_predict_api_rejects_non_positive_limit(client_with_recommendation_files):
    response = client_with_recommendation_files["client"].post(
        "/api/recommend/predict", json={"limit": 0}
    )

    assert response.status_code == 422


def test_predict_service_rejects_non_positive_limit(client_with_recommendation_files):
    temp_model_file = client_with_recommendation_files["saved_model_dir"].joinpath(
        "latest_model.joblib"
    )

    with pytest.raises(ValueError, match="limit must be positive"):
        model_service.predict_recommendations(limit=0)

    assert not temp_model_file.exists()


def test_predict_api_returns_400_for_corrupt_saved_bundle(
    client_with_recommendation_files,
):
    temp_model_file = client_with_recommendation_files["saved_model_dir"].joinpath(
        "latest_model.joblib"
    )
    temp_model_file.parent.mkdir(parents=True, exist_ok=True)
    temp_model_file.write_bytes(b"not a joblib bundle")

    client = TestClient(app, raise_server_exceptions=False)
    response = client.post("/api/recommend/predict", json={"limit": 2})

    assert response.status_code == 400
    assert "saved model bundle" in response.json()["detail"].lower()


def test_predict_api_returns_400_for_model_without_predict_proba(
    client_with_recommendation_files,
):
    temp_model_file = client_with_recommendation_files["saved_model_dir"].joinpath(
        "latest_model.joblib"
    )
    temp_model_file.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(
        {
            "model": ModelWithoutPredictProba(),
            "feature_columns": ["age", "income", "claims"],
        },
        temp_model_file,
    )

    client = TestClient(app, raise_server_exceptions=False)
    response = client.post("/api/recommend/predict", json={"limit": 2})

    assert response.status_code == 400
    assert "saved model bundle" in response.json()["detail"].lower()
    assert "predict_proba" in response.json()["detail"]


def test_predict_api_returns_400_for_invalid_feature_columns_in_saved_bundle(
    client_with_recommendation_files,
):
    model_service.train_baseline_model()
    temp_model_file = client_with_recommendation_files["saved_model_dir"].joinpath(
        "latest_model.joblib"
    )
    bundle = joblib.load(temp_model_file)
    bundle["feature_columns"] = "age"
    joblib.dump(bundle, temp_model_file)

    response = client_with_recommendation_files["client"].post(
        "/api/recommend/predict", json={"limit": 2}
    )

    assert response.status_code == 400
    assert "saved model bundle" in response.json()["detail"].lower()
    assert "feature_columns" in response.json()["detail"]


def test_predict_api_reports_missing_eval_feature_columns_during_prediction(
    client_with_recommendation_files, monkeypatch, tmp_path
):
    model_service.train_baseline_model()
    eval_data = pd.DataFrame(
        {
            "age": [28, 48],
            "claims": [0, 1],
            model_service.TARGET_COLUMN: [0, 1],
        }
    )
    eval_file = tmp_path / "eval_missing_feature.xlsx"
    eval_data.to_excel(eval_file, index=False)
    monkeypatch.setattr(model_service, "EVAL_DATA_FILE", eval_file)

    response = client_with_recommendation_files["client"].post(
        "/api/recommend/predict", json={"limit": 2}
    )

    assert response.status_code == 400
    assert "missing training feature columns" in response.json()["detail"]


def test_predict_api_reuses_existing_saved_bundle(
    client_with_recommendation_files, monkeypatch
):
    model_service.train_baseline_model()
    model_service.reset_latest_run()

    def fail_if_retrained():
        raise AssertionError("existing bundle should be reused")

    monkeypatch.setattr(model_service, "train_baseline_model", fail_if_retrained)

    response = client_with_recommendation_files["client"].post(
        "/api/recommend/predict", json={"limit": 2}
    )

    assert response.status_code == 200
    assert response.json()["count"] == 2

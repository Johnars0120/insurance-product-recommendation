import pandas as pd
from fastapi.testclient import TestClient

from app.database import configure_database, create_tables
from app.main import app
from app.services import history_service
import app.services.model_service as model_service


def _write_excel_files(tmp_path):
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
    return train_file, eval_file


def _configure_temp_environment(tmp_path, monkeypatch):
    train_file, eval_file = _write_excel_files(tmp_path)
    configure_database(f"sqlite:///{(tmp_path / 'recommendations.db').as_posix()}")
    create_tables()
    monkeypatch.setattr(model_service, "TRAIN_DATA_FILE", train_file)
    monkeypatch.setattr(model_service, "EVAL_DATA_FILE", eval_file)
    monkeypatch.setattr(model_service, "SAVED_MODEL_DIR", tmp_path / "saved_models")
    model_service.reset_latest_run()


def _recommendation_items(count):
    return [
        {
            "customer_id": str(index),
            "probability": index / (count + 1),
            "recommend_level": "medium",
            "reason": "manual test recommendation",
        }
        for index in range(1, count + 1)
    ]


def test_predict_persists_recommendation_results(tmp_path, monkeypatch):
    _configure_temp_environment(tmp_path, monkeypatch)
    client = TestClient(app)

    response = client.post("/api/recommend/predict", json={"limit": 3})

    assert response.status_code == 200
    body = response.json()
    assert body["run_id"]
    stored = history_service.list_recommendation_results(run_id=body["run_id"])
    assert len(stored) == 3
    assert stored[0]["customer_id"] == "1"
    assert stored == body["items"]


def test_predict_replaces_recommendation_results_for_same_run(
    tmp_path, monkeypatch
):
    _configure_temp_environment(tmp_path, monkeypatch)
    client = TestClient(app)
    first_response = client.post("/api/recommend/predict", json={"limit": 2})
    second_response = client.post("/api/recommend/predict", json={"limit": 3})

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    run_id = first_response.json()["run_id"]
    assert second_response.json()["run_id"] == run_id
    stored = history_service.list_recommendation_results(run_id=run_id)
    assert len(stored) == 3
    assert [item["customer_id"] for item in stored] == ["1", "2", "3"]


def test_recommendation_history_api_returns_latest_results(tmp_path, monkeypatch):
    _configure_temp_environment(tmp_path, monkeypatch)
    client = TestClient(app)
    predict_response = client.post("/api/recommend/predict", json={"limit": 2})

    response = client.get("/api/recommend/history")

    assert response.status_code == 200
    body = response.json()
    assert body["run_id"] == predict_response.json()["run_id"]
    assert body["count"] == 2
    assert body["items"] == predict_response.json()["items"]


def test_recommendation_export_returns_csv(tmp_path, monkeypatch):
    _configure_temp_environment(tmp_path, monkeypatch)
    client = TestClient(app)
    predict_response = client.post("/api/recommend/predict", json={"limit": 2})
    run_id = predict_response.json()["run_id"]

    response = client.get(f"/api/recommend/export?run_id={run_id}")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert (
        response.headers["content-disposition"]
        == "attachment; filename=recommendations.csv"
    )
    assert response.text.splitlines()[0] == (
        "customer_id,probability,recommend_level,reason"
    )


def test_recommendation_export_returns_all_rows_for_run_id(
    tmp_path, monkeypatch
):
    _configure_temp_environment(tmp_path, monkeypatch)
    run = model_service.train_baseline_model()
    history_service.save_recommendation_results(
        run["run_id"],
        _recommendation_items(105),
    )
    client = TestClient(app)

    response = client.get(f"/api/recommend/export?run_id={run['run_id']}")

    assert response.status_code == 200
    csv_lines = response.text.splitlines()
    assert len(csv_lines) == 106
    assert csv_lines[0] == "customer_id,probability,recommend_level,reason"
    assert csv_lines[-1].startswith("105,")


def test_recommendation_history_service_limit_none_returns_all_rows(
    tmp_path, monkeypatch
):
    _configure_temp_environment(tmp_path, monkeypatch)
    run = model_service.train_baseline_model()
    history_service.save_recommendation_results(
        run["run_id"],
        _recommendation_items(105),
    )

    results = model_service.list_recommendation_history(
        run_id=run["run_id"],
        limit=None,
    )

    assert len(results) == 105
    assert results[-1]["customer_id"] == "105"


def test_recommendation_history_api_returns_empty_without_history(
    tmp_path, monkeypatch
):
    _configure_temp_environment(tmp_path, monkeypatch)
    client = TestClient(app)

    response = client.get("/api/recommend/history")

    assert response.status_code == 200
    assert response.json() == {"run_id": None, "count": 0, "items": []}


def test_predict_retrains_when_bundle_run_id_is_not_persisted(
    tmp_path, monkeypatch
):
    _configure_temp_environment(tmp_path, monkeypatch)
    stale_run = model_service.train_baseline_model()
    empty_database_url = (
        f"sqlite:///{(tmp_path / 'empty-recommendations.db').as_posix()}"
    )
    configure_database(empty_database_url)
    create_tables()
    model_service.reset_latest_run()
    client = TestClient(app)

    response = client.post("/api/recommend/predict", json={"limit": 2})

    assert response.status_code == 200
    body = response.json()
    assert body["run_id"] != stale_run["run_id"]
    stored = history_service.list_recommendation_results(run_id=body["run_id"])
    assert len(stored) == 2

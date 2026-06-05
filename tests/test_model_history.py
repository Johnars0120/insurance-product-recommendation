import joblib
import pandas as pd
import pytest

from app.database import configure_database, create_tables
from app.services import history_service
import app.services.model_service as model_service


@pytest.fixture
def model_history_environment(tmp_path, monkeypatch):
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

    configure_database(f"sqlite:///{(tmp_path / 'history.db').as_posix()}")
    create_tables()
    monkeypatch.setattr(model_service, "TRAIN_DATA_FILE", train_file)
    monkeypatch.setattr(model_service, "EVAL_DATA_FILE", eval_file)
    monkeypatch.setattr(model_service, "SAVED_MODEL_DIR", tmp_path / "saved_models")
    model_service.reset_latest_run()

    return {
        "train_rows": len(train_data),
        "eval_rows": len(eval_data),
    }


def test_train_baseline_model_persists_run_and_metrics(model_history_environment):
    result = model_service.train_baseline_model("logistic_regression")

    assert result["run_id"]
    assert result["created_at"]
    assert result["train_rows"] == model_history_environment["train_rows"]
    assert result["eval_rows"] == model_history_environment["eval_rows"]

    persisted_runs = history_service.list_model_runs()

    assert len(persisted_runs) == 1
    persisted_run = persisted_runs[0]
    assert persisted_run["run_id"] == result["run_id"]
    assert persisted_run["model_name"] == "logistic_regression"
    assert persisted_run["metrics"] == result["metrics"]
    assert persisted_run["model_path"] == result["model_path"]
    assert persisted_run["created_at"] == result["created_at"]

    bundle = joblib.load(result["model_path"])
    assert bundle["run_id"] == result["run_id"]
    assert bundle["created_at"] == result["created_at"]


def test_latest_run_can_be_loaded_after_process_cache_reset(model_history_environment):
    trained_run = model_service.train_baseline_model("logistic_regression")
    model_service.reset_latest_run()

    latest_run = model_service.get_latest_run()

    assert latest_run["run_id"] == trained_run["run_id"]
    assert latest_run["model_name"] == "logistic_regression"
    assert latest_run["metrics"] == trained_run["metrics"]

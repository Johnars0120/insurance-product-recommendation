from datetime import datetime, timedelta

import joblib
import pandas as pd
import pytest

from app.database import configure_database, create_tables
from app.services import history_service
import app.services.model_service as model_service


@pytest.fixture
def model_files(tmp_path, monkeypatch):
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

    configure_database(f"sqlite:///{(tmp_path / 'model-service.db').as_posix()}")
    create_tables()
    monkeypatch.setattr(model_service, "TRAIN_DATA_FILE", train_file)
    monkeypatch.setattr(model_service, "EVAL_DATA_FILE", eval_file)
    monkeypatch.setattr(model_service, "SAVED_MODEL_DIR", saved_model_dir)
    model_service.reset_latest_run()

    return {
        "train_data": train_data,
        "eval_data": eval_data,
        "feature_columns": ["age", "income", "claims"],
        "saved_model_dir": saved_model_dir,
    }


def _assert_metric_ranges(metrics):
    for metric in ["accuracy", "precision", "recall", "f1", "auc"]:
        assert 0.0 <= metrics[metric] <= 1.0


def _history_run_summary(run_id, model_name, created_at, auc):
    return {
        "run_id": run_id,
        "model_name": model_name,
        "train_rows": 6,
        "eval_rows": 4,
        "metrics": {
            "accuracy": auc,
            "precision": auc,
            "recall": auc,
            "f1": auc,
            "auc": auc,
        },
        "model_path": f"/tmp/{run_id}.joblib",
        "created_at": created_at.isoformat(),
    }


def test_train_baseline_model_returns_metrics_and_model_path_for_supported_models(model_files):
    supported_models = ["logistic_regression", "decision_tree", "random_forest"]

    for model_name in supported_models:
        result = model_service.train_baseline_model(model_name=model_name)

        assert result["model_name"] == model_name
        assert result["run_id"]
        assert result["train_rows"] == len(model_files["train_data"])
        assert result["eval_rows"] == len(model_files["eval_data"])
        assert result["model_path"].endswith(f"{result['run_id']}.joblib")
        assert result["model_path"].startswith(str(model_files["saved_model_dir"]))
        _assert_metric_ranges(result["metrics"])


def test_train_baseline_model_saves_versioned_model_and_latest_alias(model_files):
    result = model_service.train_baseline_model(model_name="logistic_regression")

    run_model_path = model_files["saved_model_dir"] / f"{result['run_id']}.joblib"
    latest_model_path = model_files["saved_model_dir"] / "latest_model.joblib"

    assert result["model_path"] == str(run_model_path)
    assert run_model_path.exists()
    assert latest_model_path.exists()
    assert joblib.load(run_model_path)["run_id"] == result["run_id"]
    assert joblib.load(latest_model_path)["run_id"] == result["run_id"]


def test_train_baseline_model_saves_predictable_joblib_bundle(model_files):
    result = model_service.train_baseline_model(model_name="logistic_regression")

    bundle = joblib.load(result["model_path"])

    assert set(bundle) == {
        "model",
        "feature_columns",
        "model_name",
        "metrics",
        "target_column",
        "run_id",
        "created_at",
    }
    assert bundle["feature_columns"] == model_files["feature_columns"]
    assert bundle["model_name"] == "logistic_regression"
    assert bundle["metrics"] == result["metrics"]
    assert bundle["target_column"] == model_service.TARGET_COLUMN
    assert bundle["run_id"] == result["run_id"]
    assert bundle["created_at"] == result["created_at"]
    assert hasattr(bundle["model"], "predict")


def test_train_baseline_model_handles_categorical_features_and_missing_values(
    model_files, monkeypatch, tmp_path
):
    train_data = model_files["train_data"].copy()
    eval_data = model_files["eval_data"].copy()
    train_data["region"] = ["east", "west", "east", None, "north", "west"]
    eval_data["region"] = ["east", None, "north", "west"]
    train_data.loc[1, "income"] = None
    eval_data.loc[2, "claims"] = None
    train_file = tmp_path / "train_categorical.xlsx"
    eval_file = tmp_path / "eval_categorical.xlsx"
    train_data.to_excel(train_file, index=False)
    eval_data.to_excel(eval_file, index=False)
    monkeypatch.setattr(model_service, "TRAIN_DATA_FILE", train_file)
    monkeypatch.setattr(model_service, "EVAL_DATA_FILE", eval_file)

    result = model_service.train_baseline_model(model_name="logistic_regression")
    recommendations = model_service.predict_recommendations(limit=2)

    assert result["run_id"]
    assert "region" in joblib.load(result["model_path"])["feature_columns"]
    assert recommendations["count"] == 2


def test_train_baseline_model_validates_eval_feature_schema(model_files, monkeypatch, tmp_path):
    eval_data = model_files["eval_data"].drop(columns=["income"])
    eval_file = tmp_path / "eval_missing_feature.xlsx"
    eval_data.to_excel(eval_file, index=False)
    monkeypatch.setattr(model_service, "EVAL_DATA_FILE", eval_file)

    with pytest.raises(ValueError, match="missing training feature columns.*income"):
        model_service.train_baseline_model(model_name="logistic_regression")


def test_train_baseline_model_requires_both_eval_target_classes(model_files, monkeypatch, tmp_path):
    eval_data = model_files["eval_data"].copy()
    eval_data[model_service.TARGET_COLUMN] = [1, 1, 1, 1]
    eval_file = tmp_path / "eval_single_class.xlsx"
    eval_data.to_excel(eval_file, index=False)
    monkeypatch.setattr(model_service, "EVAL_DATA_FILE", eval_file)

    with pytest.raises(ValueError, match="both classes"):
        model_service.train_baseline_model(model_name="logistic_regression")


def test_history_service_lists_latest_model_run_per_model_without_recent_limit(model_files):
    base_time = datetime(2026, 1, 1, 12, 0, 0)
    expected_decision_tree = history_service.save_model_run(
        _history_run_summary("decision-tree-old", "decision_tree", base_time, 0.51)
    )
    expected_random_forest = history_service.save_model_run(
        _history_run_summary(
            "random-forest-latest",
            "random_forest",
            base_time + timedelta(seconds=30),
            0.72,
        )
    )

    expected_logistic_regression = None
    for index in range(25):
        expected_logistic_regression = history_service.save_model_run(
            _history_run_summary(
                f"logistic-regression-{index}",
                "logistic_regression",
                base_time + timedelta(minutes=index + 1),
                0.60,
            )
        )

    runs = history_service.list_latest_model_runs_by_model(
        ["logistic_regression", "decision_tree", "random_forest"]
    )
    runs_by_model = {run["model_name"]: run for run in runs}

    assert (
        runs_by_model["logistic_regression"]["run_id"]
        == expected_logistic_regression["run_id"]
    )
    assert runs_by_model["decision_tree"]["run_id"] == expected_decision_tree["run_id"]
    assert runs_by_model["random_forest"]["run_id"] == expected_random_forest["run_id"]

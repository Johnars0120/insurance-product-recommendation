import joblib
import pandas as pd
import pytest

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


def test_train_baseline_model_returns_metrics_and_model_path(model_files):
    result = model_service.train_baseline_model(model_name="logistic_regression")

    assert result["model_name"] == "logistic_regression"
    assert result["train_rows"] == len(model_files["train_data"])
    assert result["eval_rows"] == len(model_files["eval_data"])
    assert result["model_path"].endswith("latest_model.joblib")
    assert result["model_path"].startswith(str(model_files["saved_model_dir"]))
    for metric in ["accuracy", "precision", "recall", "f1", "auc"]:
        assert 0.0 <= result["metrics"][metric] <= 1.0


def test_train_baseline_model_saves_predictable_joblib_bundle(model_files):
    result = model_service.train_baseline_model(model_name="logistic_regression")

    bundle = joblib.load(result["model_path"])

    assert set(bundle) == {
        "model",
        "feature_columns",
        "model_name",
        "metrics",
        "target_column",
    }
    assert bundle["feature_columns"] == model_files["feature_columns"]
    assert bundle["model_name"] == "logistic_regression"
    assert bundle["metrics"] == result["metrics"]
    assert bundle["target_column"] == model_service.TARGET_COLUMN
    assert hasattr(bundle["model"], "predict")


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

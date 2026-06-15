import pandas as pd
import pytest
from fastapi.testclient import TestClient

from app.config import TARGET_COLUMN
from app.main import app
import app.services.dataset_service as dataset_service
import app.services.model_service as model_service
from app.services.dataset_service import build_dataset_profile, summarize_dataset


def test_build_dataset_profile_reads_training_and_eval_files():
    profile = build_dataset_profile()

    assert profile["target_column"] == "移动房车险数量"
    assert profile["train"]["rows"] == 5822
    assert profile["train"]["columns"] == 86
    assert profile["train"]["positive_count"] == 348
    assert profile["eval"]["rows"] == 4000
    assert profile["eval"]["positive_count"] == 238
    assert profile["target_positive_rate"] == profile["train"]["positive_rate"]


def test_dataset_profile_api_returns_contract():
    client = TestClient(app)

    response = client.get("/api/datasets/profile")

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {
        "target_column",
        "target_positive_rate",
        "feature_columns",
        "train",
        "eval",
    }
    assert body["target_column"] == TARGET_COLUMN
    assert "移动房车险数量" not in body["feature_columns"]
    assert set(body["train"]) == {
        "file",
        "rows",
        "columns",
        "valid_target_count",
        "positive_count",
        "negative_count",
        "positive_rate",
        "missing_value_count",
    }
    assert set(body["eval"]) == set(body["train"])
    assert body["train"]["file"] == "data.xlsx"
    assert body["eval"]["file"] == "eval.xlsx"


def test_summarize_dataset_uses_valid_targets_for_target_metrics(tmp_path):
    data_file = tmp_path / "sample.xlsx"
    pd.DataFrame(
        {
            TARGET_COLUMN: [1, 0, None, 2],
            "feature": [10, None, 30, 40],
        }
    ).to_excel(data_file, index=False)

    summary = summarize_dataset(data_file)

    assert summary["rows"] == 4
    assert summary["valid_target_count"] == 3
    assert summary["positive_count"] == 2
    assert summary["negative_count"] == 1
    assert summary["positive_rate"] == 2 / 3
    assert summary["missing_value_count"] == 2


def test_summarize_dataset_validates_target_column_presence(tmp_path):
    data_file = tmp_path / "missing_target.xlsx"
    pd.DataFrame({"feature": [1, 2]}).to_excel(data_file, index=False)

    with pytest.raises(ValueError, match=TARGET_COLUMN):
        summarize_dataset(data_file)


def _excel_bytes(dataframe):
    from io import BytesIO

    buffer = BytesIO()
    dataframe.to_excel(buffer, index=False)
    buffer.seek(0)
    return buffer.getvalue()


def test_dataset_upload_replaces_training_and_eval_files(tmp_path, monkeypatch):
    train_file = tmp_path / "data.xlsx"
    eval_file = tmp_path / "eval.xlsx"
    saved_model_dir = tmp_path / "saved_models"
    saved_model_dir.mkdir()
    stale_model = saved_model_dir / "latest_model.joblib"
    stale_model.write_text("stale", encoding="utf-8")
    train_data = pd.DataFrame(
        {
            "age": [31, 42, 53],
            "income": [5000, 7000, 9000],
            TARGET_COLUMN: [0, 1, 1],
        }
    )
    eval_data = pd.DataFrame(
        {
            "age": [28, 49],
            "income": [4800, 7600],
            TARGET_COLUMN: [0, 1],
        }
    )
    monkeypatch.setattr(dataset_service, "TRAIN_DATA_FILE", train_file)
    monkeypatch.setattr(dataset_service, "EVAL_DATA_FILE", eval_file)
    monkeypatch.setattr(model_service, "SAVED_MODEL_DIR", saved_model_dir)

    client = TestClient(app)
    response = client.post(
        "/api/datasets/upload",
        files={
            "train_file": (
                "train.xlsx",
                _excel_bytes(train_data),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ),
            "eval_file": (
                "eval.xlsx",
                _excel_bytes(eval_data),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ),
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["message"] == "Dataset files uploaded"
    assert body["profile"]["train"]["rows"] == 3
    assert body["profile"]["eval"]["rows"] == 2
    assert pd.read_excel(train_file)["age"].tolist() == [31, 42, 53]
    assert pd.read_excel(eval_file)["income"].tolist() == [4800, 7600]
    assert not stale_model.exists()


def test_dataset_upload_rejects_missing_target_column(tmp_path, monkeypatch):
    train_file = tmp_path / "data.xlsx"
    eval_file = tmp_path / "eval.xlsx"
    train_file.write_text("original train", encoding="utf-8")
    eval_file.write_text("original eval", encoding="utf-8")
    train_data = pd.DataFrame({"age": [31, 42], TARGET_COLUMN: [0, 1]})
    eval_data = pd.DataFrame({"age": [28, 49]})
    monkeypatch.setattr(dataset_service, "TRAIN_DATA_FILE", train_file)
    monkeypatch.setattr(dataset_service, "EVAL_DATA_FILE", eval_file)

    client = TestClient(app)
    response = client.post(
        "/api/datasets/upload",
        files={
            "train_file": ("train.xlsx", _excel_bytes(train_data), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
            "eval_file": ("eval.xlsx", _excel_bytes(eval_data), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
        },
    )

    assert response.status_code == 400
    assert TARGET_COLUMN in response.json()["detail"]
    assert train_file.read_text(encoding="utf-8") == "original train"
    assert eval_file.read_text(encoding="utf-8") == "original eval"


def test_dataset_upload_accepts_csv_files(tmp_path, monkeypatch):
    train_file = tmp_path / "data.xlsx"
    eval_file = tmp_path / "eval.xlsx"
    train_data = pd.DataFrame(
        {
            "age": [31, 42, 53],
            "income": [5000, 7000, 9000],
            TARGET_COLUMN: [0, 1, 1],
        }
    )
    eval_data = pd.DataFrame(
        {
            "age": [28, 49],
            "income": [4800, 7600],
            TARGET_COLUMN: [0, 1],
        }
    )
    monkeypatch.setattr(dataset_service, "TRAIN_DATA_FILE", train_file)
    monkeypatch.setattr(dataset_service, "EVAL_DATA_FILE", eval_file)

    client = TestClient(app)
    response = client.post(
        "/api/datasets/upload",
        files={
            "train_file": ("train.csv", train_data.to_csv(index=False).encode("utf-8"), "text/csv"),
            "eval_file": ("eval.csv", eval_data.to_csv(index=False).encode("utf-8"), "text/csv"),
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["profile"]["train"]["rows"] == 3
    assert body["profile"]["eval"]["rows"] == 2
    assert pd.read_excel(train_file)["age"].tolist() == [31, 42, 53]
    assert pd.read_excel(eval_file)["income"].tolist() == [4800, 7600]

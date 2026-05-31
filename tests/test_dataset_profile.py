import pandas as pd
import pytest
from fastapi.testclient import TestClient

from app.config import TARGET_COLUMN
from app.main import app
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

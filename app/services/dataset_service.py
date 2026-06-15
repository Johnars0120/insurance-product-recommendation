from pathlib import Path
import tempfile

import pandas as pd

from app.config import EVAL_DATA_FILE, TARGET_COLUMN, TRAIN_DATA_FILE
from app.services import model_service


def _read_uploaded_dataset(file_bytes, filename):
    normalized_filename = filename.lower()
    if not normalized_filename.endswith((".xlsx", ".csv")):
        raise ValueError("Only .xlsx and .csv dataset files are supported")

    try:
        from io import BytesIO

        if normalized_filename.endswith(".csv"):
            return pd.read_csv(BytesIO(file_bytes))
        return pd.read_excel(BytesIO(file_bytes))
    except Exception as exc:
        raise ValueError(f"Could not read dataset file '{filename}': {exc}") from exc


def _validate_uploaded_dataset(data, label):
    if TARGET_COLUMN not in data.columns:
        raise ValueError(f"{label} dataset must contain target column '{TARGET_COLUMN}'")


def _validate_feature_schema(train_data, eval_data):
    train_features = [column for column in train_data.columns if column != TARGET_COLUMN]
    eval_features = [column for column in eval_data.columns if column != TARGET_COLUMN]
    missing_in_eval = [column for column in train_features if column not in eval_features]
    extra_in_eval = [column for column in eval_features if column not in train_features]

    if missing_in_eval or extra_in_eval:
        details = []
        if missing_in_eval:
            details.append("missing in eval: " + ", ".join(missing_in_eval))
        if extra_in_eval:
            details.append("extra in eval: " + ", ".join(extra_in_eval))
        raise ValueError("Train and eval feature columns must match; " + "; ".join(details))


def _replace_dataset_file(file_path, data):
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(delete=False, dir=file_path.parent, suffix=file_path.suffix) as temp_file:
        temp_path = Path(temp_file.name)
    data.to_excel(temp_path, index=False)
    temp_path.replace(file_path)


def save_uploaded_datasets(train_bytes, train_filename, eval_bytes, eval_filename):
    train_data = _read_uploaded_dataset(train_bytes, train_filename)
    eval_data = _read_uploaded_dataset(eval_bytes, eval_filename)
    _validate_uploaded_dataset(train_data, "Train")
    _validate_uploaded_dataset(eval_data, "Eval")
    _validate_feature_schema(train_data, eval_data)

    _replace_dataset_file(TRAIN_DATA_FILE, train_data)
    _replace_dataset_file(EVAL_DATA_FILE, eval_data)
    model_service.clear_latest_model_file()
    return build_dataset_profile()


def summarize_dataset(file_path):
    data = pd.read_excel(file_path)

    if TARGET_COLUMN not in data.columns:
        raise ValueError(f"Target column '{TARGET_COLUMN}' not found in {file_path.name}")

    valid_targets = data[TARGET_COLUMN].dropna()
    positive_count = int((valid_targets > 0).sum())
    negative_count = int((valid_targets <= 0).sum())
    valid_target_count = int(len(valid_targets))
    rows = int(len(data))

    return {
        "file": file_path.name,
        "rows": rows,
        "columns": int(len(data.columns)),
        "valid_target_count": valid_target_count,
        "positive_count": positive_count,
        "negative_count": negative_count,
        "positive_rate": positive_count / valid_target_count
        if valid_target_count
        else 0,
        "missing_value_count": int(data.isna().sum().sum()),
        "columns_list": list(data.columns),
    }


def build_dataset_profile():
    train = summarize_dataset(TRAIN_DATA_FILE)
    eval_data = summarize_dataset(EVAL_DATA_FILE)
    feature_columns = [
        column for column in train["columns_list"] if column != TARGET_COLUMN
    ]

    train.pop("columns_list")
    eval_data.pop("columns_list")

    return {
        "target_column": TARGET_COLUMN,
        "target_positive_rate": train["positive_rate"],
        "feature_columns": feature_columns,
        "train": train,
        "eval": eval_data,
    }

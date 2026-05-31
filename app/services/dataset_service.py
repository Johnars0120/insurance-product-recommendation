import pandas as pd

from app.config import EVAL_DATA_FILE, TARGET_COLUMN, TRAIN_DATA_FILE


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

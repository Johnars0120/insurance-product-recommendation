from datetime import datetime
from uuid import uuid4

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.tree import DecisionTreeClassifier

from app.config import (
    DEFAULT_EVAL_DATA_FILE,
    DEFAULT_TRAIN_DATA_FILE,
    EVAL_DATA_FILE,
    SAVED_MODEL_DIR,
    TARGET_COLUMN,
    TRAIN_DATA_FILE,
)
from app.services import history_service


LATEST_RUN = None
SUPPORTED_MODELS = ("logistic_regression", "decision_tree", "random_forest")


def _resolve_dataset_file(runtime_file, default_file):
    if runtime_file.exists():
        return runtime_file
    return default_file


def _load_training_data():
    train_data_file = _resolve_dataset_file(TRAIN_DATA_FILE, DEFAULT_TRAIN_DATA_FILE)
    eval_data_file = _resolve_dataset_file(EVAL_DATA_FILE, DEFAULT_EVAL_DATA_FILE)
    train_data = pd.read_excel(train_data_file)
    eval_data = pd.read_excel(eval_data_file)

    if TARGET_COLUMN not in train_data.columns:
        raise ValueError(f"Target column '{TARGET_COLUMN}' not found in {train_data_file.name}")
    if TARGET_COLUMN not in eval_data.columns:
        raise ValueError(f"Target column '{TARGET_COLUMN}' not found in {eval_data_file.name}")

    feature_columns = [column for column in train_data.columns if column != TARGET_COLUMN]
    return train_data, eval_data, feature_columns


def _build_estimator(model_name):
    if model_name not in SUPPORTED_MODELS:
        raise ValueError(f"Unsupported model_name: {model_name}")

    if model_name == "logistic_regression":
        return LogisticRegression(
            class_weight="balanced",
            max_iter=1000,
            random_state=42,
        )

    if model_name == "decision_tree":
        return DecisionTreeClassifier(
            class_weight="balanced",
            max_depth=5,
            random_state=42,
        )

    return RandomForestClassifier(
        class_weight="balanced",
        n_estimators=100,
        max_depth=8,
        random_state=42,
    )


def _build_preprocessor(features):
    numeric_features = list(features.select_dtypes(include=["number", "bool"]).columns)
    categorical_features = [
        column for column in features.columns if column not in numeric_features
    ]
    transformers = []

    if numeric_features:
        transformers.append(
            (
                "numeric",
                Pipeline(
                    steps=[
                        ("imputer", SimpleImputer(strategy="median")),
                        ("scaler", StandardScaler()),
                    ]
                ),
                numeric_features,
            )
        )
    if categorical_features:
        transformers.append(
            (
                "categorical",
                Pipeline(
                    steps=[
                        ("imputer", SimpleImputer(strategy="most_frequent")),
                        ("encoder", OneHotEncoder(handle_unknown="ignore")),
                    ]
                ),
                categorical_features,
            )
        )

    if not transformers:
        raise ValueError("Training data must contain at least one feature column")

    return ColumnTransformer(transformers=transformers)


def _build_model(model_name, train_features):
    return Pipeline(
        steps=[
            ("preprocessor", _build_preprocessor(train_features)),
            ("classifier", _build_estimator(model_name)),
        ]
    )


def _target_to_binary(series):
    return (series > 0).astype(int)


def _validate_eval_features(eval_data, feature_columns):
    missing_columns = [
        column for column in feature_columns if column not in eval_data.columns
    ]
    if missing_columns:
        raise ValueError(
            "Eval data is missing training feature columns: "
            + ", ".join(missing_columns)
        )


def _latest_model_path():
    return SAVED_MODEL_DIR / "latest_model.joblib"


def _run_model_path(run_id):
    return SAVED_MODEL_DIR / f"{run_id}.joblib"


def _build_run_metadata(model_name):
    created_at = datetime.utcnow()
    timestamp = created_at.strftime("%Y%m%d%H%M%S%f")
    return {
        "run_id": f"{model_name}-{timestamp}-{uuid4().hex[:8]}",
        "created_at": created_at.isoformat(),
    }


def _recommend_level(probability):
    if probability >= 0.70:
        return "high"
    if probability >= 0.40:
        return "medium"
    return "low"


def _format_feature_hint(row):
    hints = []
    for column in ("age", "income", "claims"):
        if column in row:
            hints.append(f"{column}={row[column]}")
    if not hints:
        return "当前客户特征已纳入模型综合判断"
    return "关键特征：" + "，".join(hints)


def _build_recommendation_reason(probability, level, row):
    probability_text = f"{probability:.2%}"
    level_messages = {
        "high": "购买概率较高，建议优先跟进",
        "medium": "购买概率中等，可结合人工复核安排触达",
        "low": "购买概率较低，建议暂缓高优先级推荐",
    }
    message = level_messages.get(level, "模型已生成推荐判断")
    return f"{message}；预测概率为 {probability_text}；{_format_feature_hint(row)}"


def _load_latest_model_bundle():
    model_path = _latest_model_path()
    if not model_path.exists():
        train_baseline_model()

    try:
        bundle = joblib.load(model_path)
    except Exception as exc:
        raise ValueError(f"Saved model bundle could not be loaded: {exc}") from exc

    _validate_model_bundle(bundle)
    return bundle


def _load_prediction_bundle_and_run_id():
    bundle = _load_latest_model_bundle()
    run_id = bundle.get("run_id")
    if run_id:
        if history_service.model_run_exists(run_id):
            return bundle, run_id
        return _train_and_load_prediction_bundle()

    latest_run = history_service.get_latest_model_run()
    if latest_run is not None:
        # Legacy bundles may not carry run_id metadata; use the latest persisted
        # model run so recommendation rows still satisfy the foreign key.
        return bundle, latest_run["run_id"]

    return _train_and_load_prediction_bundle()


def _train_and_load_prediction_bundle():
    train_baseline_model()
    bundle = _load_latest_model_bundle()
    run_id = bundle.get("run_id")
    if not run_id:
        raise ValueError("Saved model bundle is missing run_id after retraining")
    return bundle, run_id


def _validate_model_bundle(bundle):
    if not isinstance(bundle, dict):
        raise ValueError("Saved model bundle must be a dict")

    required_keys = {"model", "feature_columns"}
    missing_keys = [key for key in required_keys if key not in bundle]
    if missing_keys:
        raise ValueError(
            "Saved model bundle is missing required keys: "
            + ", ".join(missing_keys)
        )

    feature_columns = bundle["feature_columns"]
    if not isinstance(feature_columns, list):
        raise ValueError("Saved model bundle feature_columns must be a list")
    if not all(isinstance(column, str) for column in feature_columns):
        raise ValueError(
            "Saved model bundle feature_columns must be a list of column names"
        )

    predict_proba = getattr(bundle["model"], "predict_proba", None)
    if not callable(predict_proba):
        raise ValueError("Saved model bundle model must provide predict_proba")


def _validate_auc_target(eval_target):
    if eval_target.nunique() < 2:
        raise ValueError("Eval target must contain both classes to compute AUC")


def train_baseline_model(model_name="logistic_regression"):
    global LATEST_RUN

    run_metadata = _build_run_metadata(model_name)
    train_data, eval_data, feature_columns = _load_training_data()

    train_features = train_data[feature_columns]
    train_target = _target_to_binary(train_data[TARGET_COLUMN])
    _validate_eval_features(eval_data, feature_columns)
    eval_features = eval_data[feature_columns]
    eval_target = _target_to_binary(eval_data[TARGET_COLUMN])
    _validate_auc_target(eval_target)
    model = _build_model(model_name, train_features)

    model.fit(train_features, train_target)

    predicted = model.predict(eval_features)
    predicted_probability = model.predict_proba(eval_features)[:, 1]
    metrics = {
        "accuracy": float(accuracy_score(eval_target, predicted)),
        "precision": float(precision_score(eval_target, predicted, zero_division=0)),
        "recall": float(recall_score(eval_target, predicted, zero_division=0)),
        "f1": float(f1_score(eval_target, predicted, zero_division=0)),
        "auc": float(roc_auc_score(eval_target, predicted_probability)),
    }

    SAVED_MODEL_DIR.mkdir(parents=True, exist_ok=True)
    model_path = _run_model_path(run_metadata["run_id"])
    latest_model_path = _latest_model_path()
    run_summary = {
        "run_id": run_metadata["run_id"],
        "model_name": model_name,
        "train_rows": int(len(train_data)),
        "eval_rows": int(len(eval_data)),
        "metrics": metrics,
        "model_path": str(model_path),
        "created_at": run_metadata["created_at"],
    }
    joblib.dump(
        {
            "model": model,
            "feature_columns": feature_columns,
            "model_name": model_name,
            "metrics": metrics,
            "target_column": TARGET_COLUMN,
            "run_id": run_summary["run_id"],
            "created_at": run_summary["created_at"],
        },
        model_path,
    )
    joblib.dump(joblib.load(model_path), latest_model_path)

    LATEST_RUN = history_service.save_model_run(run_summary)
    return LATEST_RUN


def get_latest_run():
    if LATEST_RUN is not None:
        return LATEST_RUN
    return history_service.get_latest_model_run()


def list_model_runs():
    return history_service.list_model_runs()


def compare_model_runs():
    latest_runs = history_service.list_latest_model_runs_by_model(SUPPORTED_MODELS)
    runs_by_model = {run["model_name"]: run for run in latest_runs}
    return {
        "items": [
            runs_by_model[model_name]
            for model_name in SUPPORTED_MODELS
            if model_name in runs_by_model
        ]
    }


def predict_recommendations(limit=20):
    if limit <= 0:
        raise ValueError("limit must be positive")

    bundle, run_id = _load_prediction_bundle_and_run_id()
    eval_data = pd.read_excel(_resolve_dataset_file(EVAL_DATA_FILE, DEFAULT_EVAL_DATA_FILE))
    feature_columns = bundle["feature_columns"]
    _validate_eval_features(eval_data, feature_columns)

    effective_limit = min(limit, len(eval_data))
    eval_features = eval_data[feature_columns]
    probabilities = bundle["model"].predict_proba(eval_features)[:, 1]

    items = []
    for row_index, probability in enumerate(probabilities[:effective_limit], start=1):
        probability = float(probability)
        level = _recommend_level(probability)
        row = eval_data.iloc[row_index - 1].to_dict()
        reason = _build_recommendation_reason(
            probability=probability,
            level=level,
            row=row,
        )
        items.append(
            {
                "customer_id": str(row_index),
                "probability": probability,
                "recommend_level": level,
                "reason": reason,
            }
        )

    history_service.save_recommendation_results(run_id, items)
    return {
        "run_id": run_id,
        "count": len(items),
        "items": items,
    }


def list_recommendation_history(run_id=None, limit=100):
    return history_service.list_recommendation_results(run_id=run_id, limit=limit)


def get_latest_recommendation_run_id():
    return history_service.get_latest_recommendation_run_id()


def reset_latest_run():
    global LATEST_RUN

    LATEST_RUN = None


def clear_latest_model_file():
    if SAVED_MODEL_DIR.exists():
        for pattern in ("*.joblib", "*.pkl"):
            for model_path in SAVED_MODEL_DIR.glob(pattern):
                model_path.unlink()
    reset_latest_run()

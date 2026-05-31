import joblib
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from app.config import EVAL_DATA_FILE, SAVED_MODEL_DIR, TARGET_COLUMN, TRAIN_DATA_FILE


LATEST_RUN = None
SUPPORTED_MODELS = {"logistic_regression"}
RECOMMENDATION_REASONS = {
    "high": "模型预测购买概率较高",
    "medium": "模型预测购买概率中等",
    "low": "模型预测购买概率较低",
}


def _load_training_data():
    train_data = pd.read_excel(TRAIN_DATA_FILE)
    eval_data = pd.read_excel(EVAL_DATA_FILE)

    if TARGET_COLUMN not in train_data.columns:
        raise ValueError(f"Target column '{TARGET_COLUMN}' not found in {TRAIN_DATA_FILE.name}")
    if TARGET_COLUMN not in eval_data.columns:
        raise ValueError(f"Target column '{TARGET_COLUMN}' not found in {EVAL_DATA_FILE.name}")

    feature_columns = [column for column in train_data.columns if column != TARGET_COLUMN]
    return train_data, eval_data, feature_columns


def _build_model(model_name):
    if model_name not in SUPPORTED_MODELS:
        raise ValueError(f"Unsupported model_name: {model_name}")

    return Pipeline(
        steps=[
            ("scaler", StandardScaler()),
            (
                "classifier",
                LogisticRegression(
                    class_weight="balanced",
                    max_iter=1000,
                    random_state=42,
                ),
            ),
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


def _recommend_level(probability):
    if probability >= 0.70:
        return "high"
    if probability >= 0.40:
        return "medium"
    return "low"


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

    train_data, eval_data, feature_columns = _load_training_data()
    model = _build_model(model_name)

    train_features = train_data[feature_columns]
    train_target = _target_to_binary(train_data[TARGET_COLUMN])
    _validate_eval_features(eval_data, feature_columns)
    eval_features = eval_data[feature_columns]
    eval_target = _target_to_binary(eval_data[TARGET_COLUMN])
    _validate_auc_target(eval_target)

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
    model_path = SAVED_MODEL_DIR / "latest_model.joblib"
    joblib.dump(
        {
            "model": model,
            "feature_columns": feature_columns,
            "model_name": model_name,
            "metrics": metrics,
            "target_column": TARGET_COLUMN,
        },
        model_path,
    )

    LATEST_RUN = {
        "model_name": model_name,
        "train_rows": int(len(train_data)),
        "eval_rows": int(len(eval_data)),
        "metrics": metrics,
        "model_path": str(model_path),
    }
    return LATEST_RUN


def get_latest_run():
    return LATEST_RUN


def list_model_runs():
    return [LATEST_RUN] if LATEST_RUN is not None else []


def predict_recommendations(limit=20):
    if limit <= 0:
        raise ValueError("limit must be positive")

    bundle = _load_latest_model_bundle()
    eval_data = pd.read_excel(EVAL_DATA_FILE)
    feature_columns = bundle["feature_columns"]
    _validate_eval_features(eval_data, feature_columns)

    effective_limit = min(limit, len(eval_data))
    eval_features = eval_data[feature_columns]
    probabilities = bundle["model"].predict_proba(eval_features)[:, 1]

    items = []
    for row_index, probability in enumerate(probabilities[:effective_limit], start=1):
        probability = float(probability)
        level = _recommend_level(probability)
        items.append(
            {
                "customer_id": str(row_index),
                "probability": probability,
                "recommend_level": level,
                "reason": RECOMMENDATION_REASONS[level],
            }
        )

    return {
        "count": len(items),
        "items": items,
    }


def reset_latest_run():
    global LATEST_RUN

    LATEST_RUN = None

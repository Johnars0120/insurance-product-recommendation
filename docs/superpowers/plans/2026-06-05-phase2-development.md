# Phase 2 Development Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade the Phase 1 MVP into a second-stage system that persists training and recommendation history, compares multiple models, visualizes real metrics with charts, exports recommendation results, and includes QA/documentation artifacts for course demonstration.

**Architecture:** Keep FastAPI routers thin and put business logic in services. Use SQLAlchemy + SQLite for persisted history, keep model training/prediction in `model_service.py`, expose chart-shaped API responses for the frontend, and preserve the Phase 1 rule that GET pages never trigger training or prediction.

**Tech Stack:** FastAPI, Jinja2, SQLAlchemy, SQLite, pandas, scikit-learn, joblib, ECharts, pytest, TestClient.

---

## Current Context

- Work starts from `origin/main` after Phase 1 PR merge commit `d3e8606`.
- Development branch/worktree: `codex/phase2-development`.
- Baseline verification before Phase 2: `python -m pytest -q` => `29 passed`.
- Existing model service stores only `LATEST_RUN` in process memory. Phase 2 must move user-facing history APIs to SQLite.
- Existing `app/database.py` already defines `DATABASE_FILE` and `DATABASE_URL`; `requirements.txt` already includes `sqlalchemy`.
- Runtime artifacts remain ignored: local SQLite databases, generated model files, and exported output files.

## File Structure

- `app/database.py`: SQLAlchemy engine/session setup, table creation helper, test database reconfiguration.
- `app/models/database_models.py`: SQLAlchemy ORM tables for dataset profiles, model runs, metrics, and recommendation results.
- `app/services/history_service.py`: persistence boundary for storing and reading training, metric, and recommendation history.
- `app/services/model_service.py`: model building, training, evaluation, prediction; calls `history_service` after successful operations.
- `app/routers/models.py`: model training, evaluation, run history, model comparison APIs.
- `app/routers/recommendations.py`: prediction, recommendation history, export APIs.
- `app/routers/charts.py`: chart-data APIs for dataset ratio, model metrics, and recommendation levels.
- `app/routers/pages.py`: page context only; no training or prediction side effects.
- `app/templates/*.html`: ECharts containers and UI controls.
- `tests/`: focused service/API/page tests using temporary Excel files, temporary model directories, and temporary SQLite databases.
- `docs/接口说明.md`, `docs/开发任务看板.md`, `docs/第二阶段测试记录.md`, `docs/答辩演示流程.md`: updated course-facing documentation.

## Global Rules

- Preserve existing API paths and response fields where possible.
- Add fields such as `run_id` and `created_at` without removing Phase 1 fields.
- GET page routes must not train models, score recommendations, or write database rows.
- Tests must not write to the real `insurance_recommendation.db` or real `saved_models/` directory.
- Use TDD: write/adjust failing tests first, run the targeted test to see the expected failure, implement minimal code, then run the test until it passes.
- Each implementation task ends with `python -m pytest -q`.

---

### Task 1: SQLite Foundation

**Goal:** Add reusable SQLAlchemy database setup and ORM tables without changing model behavior yet.

**Files:**
- Modify: `app/database.py`
- Create: `app/models/database_models.py`
- Modify: `app/models/__init__.py`
- Test: `tests/test_database.py`

- [ ] **Step 1: Write the failing database tests**

Create `tests/test_database.py`:

```python
from app.database import configure_database, create_tables, get_session
from app.models.database_models import (
    DatasetProfileRecord,
    ModelMetricRecord,
    ModelRunRecord,
    RecommendationResultRecord,
)


def test_create_tables_and_persist_model_run_metric_and_recommendation(tmp_path):
    database_url = f"sqlite:///{(tmp_path / 'phase2.db').as_posix()}"
    configure_database(database_url)
    create_tables()

    with get_session() as session:
        run = ModelRunRecord(
            run_id="run-001",
            model_name="logistic_regression",
            train_rows=6,
            eval_rows=4,
            model_path="saved_models/latest_model.joblib",
        )
        metric = ModelMetricRecord(
            run_id="run-001",
            accuracy=0.8,
            precision=0.7,
            recall=0.6,
            f1=0.65,
            auc=0.75,
        )
        result = RecommendationResultRecord(
            run_id="run-001",
            customer_id="1",
            probability=0.72,
            recommend_level="high",
            reason="模型预测购买概率较高",
        )
        session.add_all([run, metric, result])

    with get_session() as session:
        stored_run = session.query(ModelRunRecord).one()
        stored_metric = session.query(ModelMetricRecord).one()
        stored_result = session.query(RecommendationResultRecord).one()

    assert stored_run.run_id == "run-001"
    assert stored_run.model_name == "logistic_regression"
    assert stored_metric.auc == 0.75
    assert stored_result.recommend_level == "high"


def test_dataset_profile_record_can_store_train_and_eval_summary(tmp_path):
    database_url = f"sqlite:///{(tmp_path / 'phase2.db').as_posix()}"
    configure_database(database_url)
    create_tables()

    with get_session() as session:
        session.add(
            DatasetProfileRecord(
                dataset_name="train",
                file_name="data.xlsx",
                rows=5822,
                columns=86,
                positive_count=348,
                positive_rate=348 / 5822,
                target_column="移动房车险数量",
            )
        )

    with get_session() as session:
        profile = session.query(DatasetProfileRecord).one()

    assert profile.dataset_name == "train"
    assert profile.rows == 5822
    assert profile.positive_count == 348
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```powershell
python -m pytest tests/test_database.py -q
```

Expected: FAIL because `configure_database`, `create_tables`, `get_session`, and `app.models.database_models` do not exist yet.

- [ ] **Step 3: Implement database setup**

Modify `app/database.py` to expose these functions:

```python
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import DATABASE_URL


_engine = None
SessionLocal = None


def configure_database(database_url=DATABASE_URL):
    global _engine, SessionLocal

    connect_args = {}
    if database_url.startswith("sqlite"):
        connect_args = {"check_same_thread": False}

    _engine = create_engine(database_url, connect_args=connect_args)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)
    return _engine


def get_engine():
    global _engine

    if _engine is None:
        configure_database()
    return _engine


def create_tables():
    from app.models.database_models import Base

    Base.metadata.create_all(bind=get_engine())


@contextmanager
def get_session():
    global SessionLocal

    if SessionLocal is None:
        configure_database()
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
```

Create `app/models/database_models.py`:

```python
from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import declarative_base


Base = declarative_base()


class DatasetProfileRecord(Base):
    __tablename__ = "dataset_profiles"

    id = Column(Integer, primary_key=True, index=True)
    dataset_name = Column(String(32), nullable=False, index=True)
    file_name = Column(String(255), nullable=False)
    rows = Column(Integer, nullable=False)
    columns = Column(Integer, nullable=False)
    positive_count = Column(Integer, nullable=False)
    positive_rate = Column(Float, nullable=False)
    target_column = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class ModelRunRecord(Base):
    __tablename__ = "model_runs"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(String(64), unique=True, nullable=False, index=True)
    model_name = Column(String(64), nullable=False, index=True)
    train_rows = Column(Integer, nullable=False)
    eval_rows = Column(Integer, nullable=False)
    model_path = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)


class ModelMetricRecord(Base):
    __tablename__ = "model_metrics"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(String(64), ForeignKey("model_runs.run_id"), nullable=False, index=True)
    accuracy = Column(Float, nullable=False)
    precision = Column(Float, nullable=False)
    recall = Column(Float, nullable=False)
    f1 = Column(Float, nullable=False)
    auc = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class RecommendationResultRecord(Base):
    __tablename__ = "recommendation_results"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(String(64), ForeignKey("model_runs.run_id"), nullable=False, index=True)
    customer_id = Column(String(64), nullable=False, index=True)
    probability = Column(Float, nullable=False)
    recommend_level = Column(String(16), nullable=False, index=True)
    reason = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
```

Modify `app/models/__init__.py` so importing `app.models` is harmless:

```python
"""Database model package."""
```

- [ ] **Step 4: Run tests to verify pass**

Run:

```powershell
python -m pytest tests/test_database.py -q
```

Expected: PASS.

- [ ] **Step 5: Run full suite**

Run:

```powershell
python -m pytest -q
```

Expected: all tests pass.

---

### Task 2: Persist Training Runs and Metrics

**Goal:** Store every successful model training run and its metrics in SQLite, and have model history APIs read from SQLite.

**Files:**
- Create: `app/services/history_service.py`
- Modify: `app/services/model_service.py`
- Modify: `app/routers/models.py`
- Modify: `app/main.py`
- Test: `tests/test_model_history.py`
- Test: `tests/test_model_api.py`

- [ ] **Step 1: Write failing persistence tests**

Create `tests/test_model_history.py`:

```python
import pandas as pd
import pytest

import app.services.model_service as model_service
from app.database import configure_database, create_tables
from app.services import history_service


@pytest.fixture
def phase2_training_env(tmp_path, monkeypatch):
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

    monkeypatch.setattr(model_service, "TRAIN_DATA_FILE", train_file)
    monkeypatch.setattr(model_service, "EVAL_DATA_FILE", eval_file)
    monkeypatch.setattr(model_service, "SAVED_MODEL_DIR", tmp_path / "saved_models")
    configure_database(f"sqlite:///{(tmp_path / 'history.db').as_posix()}")
    create_tables()
    model_service.reset_latest_run()


def test_train_baseline_model_persists_run_and_metrics(phase2_training_env):
    result = model_service.train_baseline_model(model_name="logistic_regression")

    assert result["run_id"]
    assert result["created_at"]

    runs = history_service.list_model_runs()
    assert len(runs) == 1
    assert runs[0]["run_id"] == result["run_id"]
    assert runs[0]["metrics"]["auc"] == result["metrics"]["auc"]


def test_latest_run_can_be_loaded_after_process_cache_reset(phase2_training_env):
    result = model_service.train_baseline_model(model_name="logistic_regression")
    model_service.reset_latest_run()

    latest = model_service.get_latest_run()

    assert latest["run_id"] == result["run_id"]
    assert latest["model_name"] == "logistic_regression"
    assert "f1" in latest["metrics"]
```

Update `tests/test_model_api.py` expectations:

```python
def test_runs_api_returns_persisted_run_list(client_with_model_files):
    assert client_with_model_files.get("/api/models/runs").json() == []

    train_response = client_with_model_files.post(
        "/api/models/train", json={"model_name": "logistic_regression"}
    )
    response = client_with_model_files.get("/api/models/runs")

    assert response.status_code == 200
    assert response.json()[0]["run_id"] == train_response.json()["run_id"]
    assert response.json()[0]["metrics"] == train_response.json()["metrics"]
```

Also update the existing `client_with_model_files` fixture in `tests/test_model_api.py` so it configures a temporary database:

```python
from app.database import configure_database, create_tables

configure_database(f"sqlite:///{(tmp_path / 'api-history.db').as_posix()}")
create_tables()
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```powershell
python -m pytest tests/test_model_history.py tests/test_model_api.py -q
```

Expected: FAIL because `history_service` and persisted run loading do not exist.

- [ ] **Step 3: Implement history service**

Create `app/services/history_service.py`:

```python
from datetime import datetime

from app.database import create_tables, get_session
from app.models.database_models import ModelMetricRecord, ModelRunRecord


def _serialize_datetime(value):
    if value is None:
        return None
    if isinstance(value, str):
        return value
    return value.isoformat()


def _metric_dict(metric):
    if metric is None:
        return {}
    return {
        "accuracy": float(metric.accuracy),
        "precision": float(metric.precision),
        "recall": float(metric.recall),
        "f1": float(metric.f1),
        "auc": float(metric.auc),
    }


def _run_dict(run, metric):
    return {
        "run_id": run.run_id,
        "model_name": run.model_name,
        "train_rows": int(run.train_rows),
        "eval_rows": int(run.eval_rows),
        "metrics": _metric_dict(metric),
        "model_path": run.model_path,
        "created_at": _serialize_datetime(run.created_at),
    }


def save_model_run(run_summary):
    create_tables()
    with get_session() as session:
        run = ModelRunRecord(
            run_id=run_summary["run_id"],
            model_name=run_summary["model_name"],
            train_rows=run_summary["train_rows"],
            eval_rows=run_summary["eval_rows"],
            model_path=run_summary["model_path"],
            created_at=datetime.fromisoformat(run_summary["created_at"]),
        )
        metrics = run_summary["metrics"]
        metric = ModelMetricRecord(
            run_id=run_summary["run_id"],
            accuracy=metrics["accuracy"],
            precision=metrics["precision"],
            recall=metrics["recall"],
            f1=metrics["f1"],
            auc=metrics["auc"],
            created_at=datetime.fromisoformat(run_summary["created_at"]),
        )
        session.add_all([run, metric])


def list_model_runs(limit=20):
    create_tables()
    with get_session() as session:
        rows = (
            session.query(ModelRunRecord, ModelMetricRecord)
            .outerjoin(ModelMetricRecord, ModelRunRecord.run_id == ModelMetricRecord.run_id)
            .order_by(ModelRunRecord.created_at.desc())
            .limit(limit)
            .all()
        )
        return [_run_dict(run, metric) for run, metric in rows]


def get_latest_model_run():
    runs = list_model_runs(limit=1)
    return runs[0] if runs else None
```

- [ ] **Step 4: Integrate training service**

Modify `app/services/model_service.py`:

```python
from datetime import datetime
from uuid import uuid4

from app.services import history_service
```

Inside `train_baseline_model`, after metrics are computed:

```python
created_at = datetime.utcnow().replace(microsecond=0).isoformat()
run_id = f"{created_at.replace('-', '').replace(':', '').replace('T', '-')}-{model_name}-{uuid4().hex[:8]}"
```

Include `run_id` and `created_at` in the saved model bundle:

```python
{
    "model": model,
    "feature_columns": feature_columns,
    "model_name": model_name,
    "metrics": metrics,
    "target_column": TARGET_COLUMN,
    "run_id": run_id,
    "created_at": created_at,
}
```

Set and persist `LATEST_RUN`:

```python
LATEST_RUN = {
    "run_id": run_id,
    "model_name": model_name,
    "train_rows": int(len(train_data)),
    "eval_rows": int(len(eval_data)),
    "metrics": metrics,
    "model_path": str(model_path),
    "created_at": created_at,
}
history_service.save_model_run(LATEST_RUN)
return LATEST_RUN
```

Change read methods:

```python
def get_latest_run():
    if LATEST_RUN is not None:
        return LATEST_RUN
    return history_service.get_latest_model_run()


def list_model_runs():
    return history_service.list_model_runs()
```

- [ ] **Step 5: Initialize tables during startup**

Modify `app/main.py`:

```python
from app.database import create_tables

create_tables()
```

Place `create_tables()` after `app` creation and before router inclusion.

- [ ] **Step 6: Run tests to verify pass**

Run:

```powershell
python -m pytest tests/test_model_history.py tests/test_model_api.py -q
```

Expected: PASS.

- [ ] **Step 7: Run full suite**

Run:

```powershell
python -m pytest -q
```

Expected: all tests pass.

---

### Task 3: Model Comparison

**Goal:** Add decision tree and random forest training, and expose an API that returns latest metrics per model for comparison charts.

**Files:**
- Modify: `app/services/model_service.py`
- Modify: `app/services/history_service.py`
- Modify: `app/routers/models.py`
- Modify: `app/routers/pages.py`
- Test: `tests/test_model_service.py`
- Test: `tests/test_model_api.py`

- [ ] **Step 1: Write failing model comparison tests**

Update `tests/test_model_service.py` with:

```python
def test_train_supported_phase2_models_returns_metrics(training_files):
    for model_name in ["logistic_regression", "decision_tree", "random_forest"]:
        result = train_baseline_model(model_name=model_name)

        assert result["model_name"] == model_name
        assert result["run_id"]
        for metric in ["accuracy", "precision", "recall", "f1", "auc"]:
            assert 0.0 <= result["metrics"][metric] <= 1.0
```

Update `tests/test_model_api.py` with:

```python
def test_compare_api_returns_latest_metrics_for_each_model(client_with_model_files):
    for model_name in ["logistic_regression", "decision_tree", "random_forest"]:
        train_response = client_with_model_files.post(
            "/api/models/train", json={"model_name": model_name}
        )
        assert train_response.status_code == 200

    response = client_with_model_files.get("/api/models/compare")

    assert response.status_code == 200
    body = response.json()
    assert [item["model_name"] for item in body["items"]] == [
        "logistic_regression",
        "decision_tree",
        "random_forest",
    ]
    for item in body["items"]:
        assert item["run_id"]
        assert "auc" in item["metrics"]
```

Change the unsupported-model test so it uses a truly unsupported name:

```python
def test_train_api_rejects_unsupported_model_name(client_with_model_files):
    response = client_with_model_files.post(
        "/api/models/train", json={"model_name": "xgboost"}
    )

    assert response.status_code == 400
    assert "Unsupported model_name" in response.json()["detail"]
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```powershell
python -m pytest tests/test_model_service.py tests/test_model_api.py -q
```

Expected: FAIL because `decision_tree`, `random_forest`, and `/api/models/compare` are not implemented.

- [ ] **Step 3: Implement model builders**

Modify `app/services/model_service.py`:

```python
from sklearn.ensemble import RandomForestClassifier
from sklearn.tree import DecisionTreeClassifier
```

Set:

```python
SUPPORTED_MODELS = {"logistic_regression", "decision_tree", "random_forest"}
```

Change `_build_model`:

```python
def _build_model(model_name):
    if model_name == "logistic_regression":
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
    if model_name == "decision_tree":
        return DecisionTreeClassifier(
            class_weight="balanced",
            max_depth=5,
            random_state=42,
        )
    if model_name == "random_forest":
        return RandomForestClassifier(
            class_weight="balanced",
            n_estimators=100,
            max_depth=8,
            random_state=42,
        )
    raise ValueError(f"Unsupported model_name: {model_name}")
```

- [ ] **Step 4: Add comparison history query**

Add to `app/services/history_service.py`:

```python
def list_latest_model_metrics_by_model():
    create_tables()
    latest_by_model = {}
    for run in list_model_runs(limit=100):
        model_name = run["model_name"]
        if model_name not in latest_by_model:
            latest_by_model[model_name] = run
    ordered_names = ["logistic_regression", "decision_tree", "random_forest"]
    return [
        latest_by_model[name]
        for name in ordered_names
        if name in latest_by_model
    ]
```

Add to `app/services/model_service.py`:

```python
def compare_model_runs():
    return {
        "items": history_service.list_latest_model_metrics_by_model()
    }
```

- [ ] **Step 5: Add compare API and page model list**

Modify `app/routers/models.py`:

```python
@router.get("/compare")
def compare_models():
    return model_service.compare_model_runs()
```

Modify `app/routers/pages.py` train page context:

```python
"available_models": ["logistic_regression", "decision_tree", "random_forest"],
```

- [ ] **Step 6: Run tests to verify pass**

Run:

```powershell
python -m pytest tests/test_model_service.py tests/test_model_api.py -q
```

Expected: PASS.

- [ ] **Step 7: Run full suite**

Run:

```powershell
python -m pytest -q
```

Expected: all tests pass.

---

### Task 4: Recommendation History and Export

**Goal:** Save prediction results to SQLite, expose recommendation history, and export latest or selected run results as CSV.

**Files:**
- Modify: `app/services/history_service.py`
- Modify: `app/services/model_service.py`
- Modify: `app/routers/recommendations.py`
- Test: `tests/test_recommendation_history.py`
- Test: `tests/test_recommendation_api.py`

- [ ] **Step 1: Write failing recommendation history tests**

Create `tests/test_recommendation_history.py`:

```python
import pandas as pd
import pytest
from fastapi.testclient import TestClient

import app.services.model_service as model_service
from app.database import configure_database, create_tables
from app.main import app
from app.services import history_service


@pytest.fixture
def recommendation_history_env(tmp_path, monkeypatch):
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
    monkeypatch.setattr(model_service, "TRAIN_DATA_FILE", train_file)
    monkeypatch.setattr(model_service, "EVAL_DATA_FILE", eval_file)
    monkeypatch.setattr(model_service, "SAVED_MODEL_DIR", tmp_path / "saved_models")
    configure_database(f"sqlite:///{(tmp_path / 'recommendations.db').as_posix()}")
    create_tables()
    model_service.reset_latest_run()
    return TestClient(app)


def test_predict_persists_recommendation_results(recommendation_history_env):
    response = recommendation_history_env.post("/api/recommend/predict", json={"limit": 3})

    assert response.status_code == 200
    body = response.json()
    assert body["run_id"]

    stored = history_service.list_recommendation_results(run_id=body["run_id"])
    assert len(stored) == 3
    assert stored[0]["customer_id"] == "1"


def test_recommendation_history_api_returns_latest_results(recommendation_history_env):
    predict_response = recommendation_history_env.post(
        "/api/recommend/predict", json={"limit": 2}
    )

    response = recommendation_history_env.get("/api/recommend/history")

    assert response.status_code == 200
    assert response.json()["run_id"] == predict_response.json()["run_id"]
    assert response.json()["count"] == 2


def test_recommendation_export_returns_csv(recommendation_history_env):
    predict_response = recommendation_history_env.post(
        "/api/recommend/predict", json={"limit": 2}
    )

    response = recommendation_history_env.get(
        f"/api/recommend/export?run_id={predict_response.json()['run_id']}"
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "customer_id,probability,recommend_level,reason" in response.text
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```powershell
python -m pytest tests/test_recommendation_history.py tests/test_recommendation_api.py -q
```

Expected: FAIL because recommendation history and export are not implemented.

- [ ] **Step 3: Implement recommendation persistence helpers**

Add to `app/services/history_service.py`:

```python
from app.models.database_models import RecommendationResultRecord


def save_recommendation_results(run_id, items):
    create_tables()
    with get_session() as session:
        for item in items:
            session.add(
                RecommendationResultRecord(
                    run_id=run_id,
                    customer_id=item["customer_id"],
                    probability=item["probability"],
                    recommend_level=item["recommend_level"],
                    reason=item["reason"],
                )
            )


def get_latest_recommendation_run_id():
    create_tables()
    with get_session() as session:
        row = (
            session.query(RecommendationResultRecord.run_id)
            .order_by(RecommendationResultRecord.created_at.desc())
            .first()
        )
        return row[0] if row else None


def list_recommendation_results(run_id=None, limit=100):
    create_tables()
    effective_run_id = run_id or get_latest_recommendation_run_id()
    if effective_run_id is None:
        return []
    with get_session() as session:
        rows = (
            session.query(RecommendationResultRecord)
            .filter(RecommendationResultRecord.run_id == effective_run_id)
            .order_by(RecommendationResultRecord.id.asc())
            .limit(limit)
            .all()
        )
        return [
            {
                "customer_id": row.customer_id,
                "probability": float(row.probability),
                "recommend_level": row.recommend_level,
                "reason": row.reason,
            }
            for row in rows
        ]
```

- [ ] **Step 4: Persist prediction results**

Modify `app/services/model_service.py` in `predict_recommendations`:

```python
run_id = bundle.get("run_id")
if run_id is None:
    latest_run = get_latest_run()
    run_id = latest_run["run_id"] if latest_run else "adhoc-recommendation"
```

Return and persist:

```python
history_service.save_recommendation_results(run_id, items)
return {
    "run_id": run_id,
    "count": len(items),
    "items": items,
}
```

- [ ] **Step 5: Add history and export APIs**

Modify `app/routers/recommendations.py`:

```python
import csv
from io import StringIO

from fastapi import Query
from fastapi.responses import Response


@router.get("/history")
def get_recommendation_history(
    run_id: str | None = None,
    limit: int = Query(default=100, gt=0),
):
    items = model_service.list_recommendation_history(run_id=run_id, limit=limit)
    effective_run_id = run_id or model_service.get_latest_recommendation_run_id()
    return {
        "run_id": effective_run_id,
        "count": len(items),
        "items": items,
    }


@router.get("/export")
def export_recommendations(run_id: str | None = None):
    items = model_service.list_recommendation_history(run_id=run_id, limit=10000)
    output = StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=["customer_id", "probability", "recommend_level", "reason"],
    )
    writer.writeheader()
    writer.writerows(items)
    return Response(
        content=output.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=recommendations.csv"},
    )
```

Add wrapper functions to `app/services/model_service.py`:

```python
def list_recommendation_history(run_id=None, limit=100):
    return history_service.list_recommendation_results(run_id=run_id, limit=limit)


def get_latest_recommendation_run_id():
    return history_service.get_latest_recommendation_run_id()
```

- [ ] **Step 6: Run tests to verify pass**

Run:

```powershell
python -m pytest tests/test_recommendation_history.py tests/test_recommendation_api.py -q
```

Expected: PASS.

- [ ] **Step 7: Run full suite**

Run:

```powershell
python -m pytest -q
```

Expected: all tests pass.

---

### Task 5: Chart APIs and ECharts Pages

**Goal:** Add chart-data APIs and update pages so the second-stage demo can show dataset ratio, model metrics comparison, and recommendation level distribution.

**Files:**
- Create: `app/routers/charts.py`
- Modify: `app/main.py`
- Modify: `app/templates/base.html`
- Modify: `app/templates/data.html`
- Modify: `app/templates/train.html`
- Modify: `app/templates/evaluate.html`
- Modify: `app/templates/recommend.html`
- Modify: `app/static/css/main.css`
- Test: `tests/test_charts_api.py`
- Test: `tests/test_pages.py`

- [ ] **Step 1: Write failing chart API tests**

Create `tests/test_charts_api.py`:

```python
import pandas as pd
import pytest
from fastapi.testclient import TestClient

import app.services.dataset_service as dataset_service
import app.services.model_service as model_service
from app.database import configure_database, create_tables
from app.main import app


@pytest.fixture
def chart_client(tmp_path, monkeypatch):
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

    monkeypatch.setattr(model_service, "TRAIN_DATA_FILE", train_file)
    monkeypatch.setattr(model_service, "EVAL_DATA_FILE", eval_file)
    monkeypatch.setattr(model_service, "SAVED_MODEL_DIR", tmp_path / "saved_models")
    monkeypatch.setattr(dataset_service, "TRAIN_DATA_FILE", train_file)
    monkeypatch.setattr(dataset_service, "EVAL_DATA_FILE", eval_file)
    configure_database(f"sqlite:///{(tmp_path / 'charts.db').as_posix()}")
    create_tables()
    model_service.reset_latest_run()
    return TestClient(app)


def test_dataset_chart_api_returns_positive_negative_counts(chart_client):
    response = chart_client.get("/api/charts/dataset")

    assert response.status_code == 200
    body = response.json()
    assert body["series"][0]["name"] == "正样本"
    assert body["series"][0]["value"] == 3
    assert body["series"][1]["name"] == "负样本"
    assert body["series"][1]["value"] == 3


def test_model_metrics_chart_api_returns_compare_items(chart_client):
    chart_client.post("/api/models/train", json={"model_name": "logistic_regression"})

    response = chart_client.get("/api/charts/model-metrics")

    assert response.status_code == 200
    assert response.json()["models"] == ["logistic_regression"]
    assert "auc" in response.json()["metrics"]


def test_recommend_level_chart_api_returns_level_counts(chart_client):
    chart_client.post("/api/recommend/predict", json={"limit": 4})

    response = chart_client.get("/api/charts/recommend-levels")

    assert response.status_code == 200
    body = response.json()
    assert {"high", "medium", "low"} <= set(body["levels"])
    assert sum(body["counts"]) == 4
```

Update `tests/test_pages.py`:

```python
def test_second_stage_pages_include_chart_containers():
    client = TestClient(app)

    response = client.get("/data")
    assert response.status_code == 200
    assert 'id="dataset-chart"' in response.text

    response = client.get("/evaluate")
    assert response.status_code == 200
    assert 'id="metrics-chart"' in response.text

    response = client.get("/recommend")
    assert response.status_code == 200
    assert 'id="recommend-level-chart"' in response.text
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```powershell
python -m pytest tests/test_charts_api.py tests/test_pages.py -q
```

Expected: FAIL because chart APIs and chart containers do not exist.

- [ ] **Step 3: Implement chart APIs**

Create `app/routers/charts.py`:

```python
from collections import Counter

from fastapi import APIRouter

from app.services.dataset_service import build_dataset_profile
from app.services import model_service


router = APIRouter(prefix="/api/charts", tags=["charts"])


@router.get("/dataset")
def dataset_chart():
    profile = build_dataset_profile()
    positive = profile["train"]["positive_count"]
    total = profile["train"]["rows"]
    negative = total - positive
    return {
        "series": [
            {"name": "正样本", "value": positive},
            {"name": "负样本", "value": negative},
        ]
    }


@router.get("/model-metrics")
def model_metrics_chart():
    comparison = model_service.compare_model_runs()["items"]
    metric_names = ["accuracy", "precision", "recall", "f1", "auc"]
    return {
        "models": [item["model_name"] for item in comparison],
        "metrics": {
            metric: [item["metrics"].get(metric, 0.0) for item in comparison]
            for metric in metric_names
        },
    }


@router.get("/recommend-levels")
def recommend_levels_chart():
    items = model_service.list_recommendation_history(limit=10000)
    counts = Counter(item["recommend_level"] for item in items)
    levels = ["high", "medium", "low"]
    return {
        "levels": levels,
        "counts": [counts.get(level, 0) for level in levels],
    }
```

Modify `app/main.py`:

```python
from app.routers import charts, datasets, models, pages, recommendations

app.include_router(charts.router)
```

- [ ] **Step 4: Add ECharts containers and scripts**

Modify `app/templates/base.html` before `</body>`:

```html
<script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
{% block scripts %}{% endblock %}
```

Modify `app/templates/data.html`:

```html
<section class="panel">
  <h2>样本比例</h2>
  <div id="dataset-chart" class="chart-panel"></div>
</section>

{% block scripts %}
<script>
fetch("/api/charts/dataset")
  .then((response) => response.json())
  .then((data) => {
    const chart = echarts.init(document.getElementById("dataset-chart"));
    chart.setOption({
      tooltip: { trigger: "item" },
      series: [{ type: "pie", radius: "60%", data: data.series }]
    });
  });
</script>
{% endblock %}
```

Modify `app/templates/evaluate.html`:

```html
<section class="panel">
  <h2>模型指标对比</h2>
  <div id="metrics-chart" class="chart-panel"></div>
</section>

{% block scripts %}
<script>
fetch("/api/charts/model-metrics")
  .then((response) => response.json())
  .then((data) => {
    const chart = echarts.init(document.getElementById("metrics-chart"));
    const series = Object.keys(data.metrics).map((metric) => ({
      name: metric,
      type: "bar",
      data: data.metrics[metric]
    }));
    chart.setOption({
      tooltip: { trigger: "axis" },
      legend: {},
      xAxis: { type: "category", data: data.models },
      yAxis: { type: "value", min: 0, max: 1 },
      series
    });
  });
</script>
{% endblock %}
```

Modify `app/templates/recommend.html`:

```html
<section class="panel">
  <h2>推荐等级分布</h2>
  <div id="recommend-level-chart" class="chart-panel"></div>
</section>

{% block scripts %}
<script>
fetch("/api/charts/recommend-levels")
  .then((response) => response.json())
  .then((data) => {
    const chart = echarts.init(document.getElementById("recommend-level-chart"));
    chart.setOption({
      tooltip: { trigger: "axis" },
      xAxis: { type: "category", data: data.levels },
      yAxis: { type: "value" },
      series: [{ type: "bar", data: data.counts }]
    });
  });
</script>
{% endblock %}
```

Modify `app/static/css/main.css`:

```css
.chart-panel {
  width: 100%;
  min-height: 320px;
}
```

If templates already have sections with similar names, integrate these snippets into the existing structure instead of duplicating page cards.

- [ ] **Step 5: Run tests to verify pass**

Run:

```powershell
python -m pytest tests/test_charts_api.py tests/test_pages.py -q
```

Expected: PASS.

- [ ] **Step 6: Run full suite**

Run:

```powershell
python -m pytest -q
```

Expected: all tests pass.

---

### Task 6: Documentation and QA Handoff

**Goal:** Update project-facing documentation so group members know what Phase 2 added, how to test it, and how to demonstrate it.

**Files:**
- Modify: `README.md`
- Modify: `docs/接口说明.md`
- Modify: `docs/开发任务看板.md`
- Create: `docs/第二阶段测试记录.md`
- Create: `docs/答辩演示流程.md`
- Test: `python -m pytest -q`

- [ ] **Step 1: Write the documentation content**

Update `docs/接口说明.md` so it includes these Phase 2 APIs:

```markdown
| `/api/models/compare` | GET | 返回各模型最近一次训练指标，用于模型对比图 |
| `/api/recommend/history` | GET | 查询最近一次或指定 run_id 的推荐结果 |
| `/api/recommend/export` | GET | 导出最近一次或指定 run_id 的推荐结果 CSV |
| `/api/charts/dataset` | GET | 返回训练集正负样本比例图数据 |
| `/api/charts/model-metrics` | GET | 返回模型指标对比图数据 |
| `/api/charts/recommend-levels` | GET | 返回推荐等级分布图数据 |
```

Update `docs/开发任务看板.md` so Phase 2 completed items are checked when implementation is present:

```markdown
- [x] 设计 SQLite 表：数据集、训练记录、指标记录、预测结果
- [x] 训练决策树模型
- [x] 训练随机森林模型
- [x] 添加正负样本比例图
- [x] 添加模型指标对比图
- [x] 添加推荐等级分布图
- [x] 编写测试记录模板
- [x] 整理答辩演示流程
```

Create `docs/第二阶段测试记录.md`:

```markdown
# 第二阶段测试记录

## 测试环境

- Python 版本：以本机 `python --version` 输出为准
- 启动命令：`uvicorn app.main:app --reload --host 127.0.0.1 --port 8000`
- 自动化测试命令：`python -m pytest -q`

## 自动化测试

| 日期 | 命令 | 结果 | 说明 |
| --- | --- | --- | --- |
| 2026-06-05 | `python -m pytest -q` | 通过 | 第二阶段功能回归测试 |

## 页面检查

| 页面 | 检查内容 | 结果 |
| --- | --- | --- |
| `/` | 首页可打开，显示系统状态 | 待截图 |
| `/data` | 数据概览和样本比例图 | 待截图 |
| `/train` | 三种模型可训练 | 待截图 |
| `/evaluate` | 模型指标对比图 | 待截图 |
| `/recommend` | 推荐等级分布和导出 | 待截图 |
| `/docs` | API 文档可打开 | 待截图 |
```

Create `docs/答辩演示流程.md`:

```markdown
# 答辩演示流程

## 演示顺序

1. 启动系统：`uvicorn app.main:app --reload --host 127.0.0.1 --port 8000`
2. 打开首页 `/`，说明系统目标和功能模块。
3. 打开数据页 `/data`，展示训练集、评估集和正负样本比例。
4. 打开训练页 `/train`，分别训练逻辑回归、决策树和随机森林。
5. 打开评估页 `/evaluate`，展示 Accuracy、Precision、Recall、F1、AUC 对比。
6. 打开推荐页 `/recommend`，生成推荐结果并查看推荐等级分布。
7. 调用 `/api/recommend/export`，展示推荐结果导出文件。
8. 打开 `/docs`，说明接口设计和模块分工。

## 讲解重点

- 系统使用历史数据训练模型，输出客户购买保险产品的概率。
- 因为正样本比例较低，评估时不能只看 Accuracy，还要关注 Recall、F1 和 AUC。
- 第二阶段增加了 SQLite 持久化，训练和推荐结果可以保留。
- 第二阶段增加了多模型对比，便于选择更合适的推荐模型。
- 第二阶段增加了图表和导出功能，便于展示和业务使用。
```

Update `README.md` to mention:

```markdown
第二阶段新增：

- SQLite 持久化训练记录、指标记录和推荐结果
- 逻辑回归、决策树、随机森林模型对比
- ECharts 数据概览、模型指标、推荐等级图表
- 推荐结果 CSV 导出
- 第二阶段测试记录和答辩演示流程
```

- [ ] **Step 2: Run docs sanity checks**

Run:

```powershell
rg "占位" README.md docs
```

Expected: no unintended placeholder notes. The planned `待截图` entries in `docs/第二阶段测试记录.md` are acceptable because screenshots are collected manually during final demonstration.

- [ ] **Step 3: Run full suite**

Run:

```powershell
python -m pytest -q
```

Expected: all tests pass.

---

### Task 7: Final Verification

**Goal:** Verify the complete Phase 2 branch and prepare a clean handoff.

**Files:**
- No new files expected.

- [ ] **Step 1: Inspect git status**

Run:

```powershell
git status --short --branch
```

Expected: branch is `codex/phase2-development`; only intentional committed or uncommitted Phase 2 files are present.

- [ ] **Step 2: Run full automated tests**

Run:

```powershell
python -m pytest -q
```

Expected: all tests pass.

- [ ] **Step 3: Smoke-check app import**

Run:

```powershell
python -c "from app.main import app; print(app.title)"
```

Expected: prints `保险产品智能推荐系统`.

- [ ] **Step 4: Smoke-check core APIs with TestClient**

Run:

```powershell
python - <<'PY'
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
print(client.get('/health').status_code)
print(client.get('/api/datasets/profile').status_code)
print(client.get('/api/charts/dataset').status_code)
PY
```

Expected: three `200` lines.

- [ ] **Step 5: Review generated/runtime artifacts**

Run:

```powershell
git status --ignored --short
```

Expected: generated `.db`, `saved_models/*.joblib`, and export/output artifacts are ignored and not staged.

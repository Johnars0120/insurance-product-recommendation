from datetime import datetime

from app.database import get_session
from app.models.database_models import ModelMetricRecord, ModelRunRecord


METRIC_FIELDS = ("accuracy", "precision", "recall", "f1", "auc")


def _parse_created_at(value):
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(value)


def _serialize_run(run_record, metric_record):
    return {
        "run_id": run_record.run_id,
        "model_name": run_record.model_name,
        "train_rows": run_record.train_rows,
        "eval_rows": run_record.eval_rows,
        "metrics": {
            field: float(getattr(metric_record, field)) for field in METRIC_FIELDS
        },
        "model_path": run_record.model_path,
        "created_at": run_record.created_at.isoformat(),
    }


def save_model_run(run_summary):
    metrics = run_summary["metrics"]
    created_at = _parse_created_at(run_summary["created_at"])

    with get_session() as session:
        run_record = ModelRunRecord(
            run_id=run_summary["run_id"],
            model_name=run_summary["model_name"],
            train_rows=run_summary["train_rows"],
            eval_rows=run_summary["eval_rows"],
            model_path=run_summary["model_path"],
            created_at=created_at,
        )
        session.add(run_record)
        session.flush()
        metric_record = ModelMetricRecord(
            run_id=run_summary["run_id"],
            accuracy=float(metrics["accuracy"]),
            precision=float(metrics["precision"]),
            recall=float(metrics["recall"]),
            f1=float(metrics["f1"]),
            auc=float(metrics["auc"]),
            created_at=created_at,
        )
        session.add(metric_record)

    return _serialize_run(run_record, metric_record)


def list_model_runs(limit=20):
    with get_session() as session:
        rows = (
            session.query(ModelRunRecord, ModelMetricRecord)
            .join(ModelMetricRecord, ModelMetricRecord.run_id == ModelRunRecord.run_id)
            .order_by(ModelRunRecord.created_at.desc(), ModelRunRecord.id.desc())
            .limit(limit)
            .all()
        )

    return [
        _serialize_run(run_record, metric_record)
        for run_record, metric_record in rows
    ]


def list_latest_model_runs_by_model(model_names=None):
    model_names_filter = None
    if model_names is not None:
        model_names_filter = list(model_names)
        if not model_names_filter:
            return []

    with get_session() as session:
        query = (
            session.query(ModelRunRecord, ModelMetricRecord)
            .join(ModelMetricRecord, ModelMetricRecord.run_id == ModelRunRecord.run_id)
            .order_by(ModelRunRecord.created_at.desc(), ModelRunRecord.id.desc())
        )
        if model_names_filter is not None:
            query = query.filter(ModelRunRecord.model_name.in_(model_names_filter))
        rows = query.all()

    latest_runs_by_model = {}
    for run_record, metric_record in rows:
        if run_record.model_name not in latest_runs_by_model:
            latest_runs_by_model[run_record.model_name] = _serialize_run(
                run_record,
                metric_record,
            )

    return list(latest_runs_by_model.values())


def get_latest_model_run():
    runs = list_model_runs(limit=1)
    if not runs:
        return None
    return runs[0]

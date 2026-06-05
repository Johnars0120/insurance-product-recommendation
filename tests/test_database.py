import pytest
from sqlalchemy.exc import IntegrityError

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
            reason="high purchase probability",
        )
        session.add(run)
        session.flush()
        session.add_all([metric, result])

    with get_session() as session:
        stored_run = session.query(ModelRunRecord).one()
        stored_metric = session.query(ModelMetricRecord).one()
        stored_result = session.query(RecommendationResultRecord).one()

    assert stored_run.run_id == "run-001"
    assert stored_run.model_name == "logistic_regression"
    assert stored_run.train_rows == 6
    assert stored_metric.auc == 0.75
    assert stored_result.customer_id == "1"
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
                target_column="target",
            )
        )

    with get_session() as session:
        profile = session.query(DatasetProfileRecord).one()

    assert profile.dataset_name == "train"
    assert profile.file_name == "data.xlsx"
    assert profile.rows == 5822
    assert profile.positive_count == 348
    assert profile.target_column == "target"


def test_orphan_metric_and_recommendation_records_fail_with_integrity_error(tmp_path):
    database_url = f"sqlite:///{(tmp_path / 'phase2.db').as_posix()}"
    configure_database(database_url)
    create_tables()

    with pytest.raises(IntegrityError):
        with get_session() as session:
            session.add(
                ModelMetricRecord(
                    run_id="missing-run",
                    accuracy=0.8,
                    precision=0.7,
                    recall=0.6,
                    f1=0.65,
                    auc=0.75,
                )
            )

    with pytest.raises(IntegrityError):
        with get_session() as session:
            session.add(
                RecommendationResultRecord(
                    run_id="missing-run",
                    customer_id="1",
                    probability=0.72,
                    recommend_level="high",
                    reason="high purchase probability",
                )
            )


def test_reconfiguring_database_disposes_previous_sqlite_engine(tmp_path):
    first_db = tmp_path / "first.db"
    second_db = tmp_path / "second.db"
    # Keep a live reference so unlink proves configure_database disposed the old pool.
    old_engine = configure_database(f"sqlite:///{first_db.as_posix()}")
    create_tables()

    with get_session() as session:
        session.add(
            DatasetProfileRecord(
                dataset_name="train",
                file_name="data.xlsx",
                rows=10,
                columns=3,
                positive_count=2,
                positive_rate=0.2,
                target_column="target",
            )
        )

    configure_database(f"sqlite:///{second_db.as_posix()}")
    create_tables()

    first_db.unlink()
    assert not first_db.exists()
    old_engine.dispose()


def test_model_metric_run_id_is_unique_per_model_run(tmp_path):
    database_url = f"sqlite:///{(tmp_path / 'phase2.db').as_posix()}"
    configure_database(database_url)
    create_tables()

    with get_session() as session:
        session.add(
            ModelRunRecord(
                run_id="run-001",
                model_name="logistic_regression",
                train_rows=6,
                eval_rows=4,
                model_path="saved_models/latest_model.joblib",
            )
        )

    with get_session() as session:
        session.add(
            ModelMetricRecord(
                run_id="run-001",
                accuracy=0.8,
                precision=0.7,
                recall=0.6,
                f1=0.65,
                auc=0.75,
            )
        )

    with pytest.raises(IntegrityError):
        with get_session() as session:
            session.add(
                ModelMetricRecord(
                    run_id="run-001",
                    accuracy=0.9,
                    precision=0.8,
                    recall=0.7,
                    f1=0.75,
                    auc=0.85,
                )
            )

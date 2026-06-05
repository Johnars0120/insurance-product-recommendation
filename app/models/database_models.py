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
    run_id = Column(
        String(64),
        ForeignKey("model_runs.run_id"),
        nullable=False,
        index=True,
    )
    accuracy = Column(Float, nullable=False)
    precision = Column(Float, nullable=False)
    recall = Column(Float, nullable=False)
    f1 = Column(Float, nullable=False)
    auc = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class RecommendationResultRecord(Base):
    __tablename__ = "recommendation_results"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(
        String(64),
        ForeignKey("model_runs.run_id"),
        nullable=False,
        index=True,
    )
    customer_id = Column(String(64), nullable=False, index=True)
    probability = Column(Float, nullable=False)
    recommend_level = Column(String(16), nullable=False, index=True)
    reason = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

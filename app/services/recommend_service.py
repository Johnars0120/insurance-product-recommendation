"""Recommendation service: save results, query history, export CSV."""

import csv
import io
import uuid
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.recommendation import Recommendation


def _determine_level(probability: float) -> str:
    """Map probability to recommend level."""
    if probability >= 0.70:
        return "high"
    elif probability >= 0.40:
        return "medium"
    else:
        return "low"


def _generate_reason(probability: float, level: str) -> str:
    """Generate a short reason text based on probability and level."""
    reasons = {
        "high": f"模型预测购买概率为 {probability:.2f}，推荐优先跟进",
        "medium": f"模型预测购买概率为 {probability:.2f}，可适度关注",
        "low": f"模型预测购买概率为 {probability:.2f}，暂不推荐",
    }
    return reasons.get(level, f"模型预测购买概率 {probability:.2f}")


def save_results(
    predictions: list[dict],
    batch_id: Optional[str] = None,
) -> dict:
    """
    Save a batch of recommendation results to the database.

    Each prediction dict should contain:
        - customer_id: str
        - probability: float
        - recommend_level: str (optional, auto-generated if missing)
        - reason: str (optional, auto-generated if missing)
    """
    if batch_id is None:
        batch_id = uuid.uuid4().hex[:12]

    db: Session = SessionLocal()
    try:
        saved_count = 0
        for pred in predictions:
            probability = float(pred["probability"])
            level = pred.get("recommend_level") or _determine_level(probability)
            reason = pred.get("reason") or _generate_reason(probability, level)

            record = Recommendation(
                customer_id=str(pred["customer_id"]),
                probability=probability,
                recommend_level=level,
                reason=reason,
                batch_id=batch_id,
            )
            db.add(record)
            saved_count += 1

        db.commit()

        # 统计本批次各级别数量
        stats = (
            db.query(
                Recommendation.recommend_level,
                func.count(Recommendation.id),
            )
            .filter(Recommendation.batch_id == batch_id)
            .group_by(Recommendation.recommend_level)
            .all()
        )
        level_counts = {level: count for level, count in stats}

        return {
            "batch_id": batch_id,
            "saved_count": saved_count,
            "level_counts": level_counts,
        }
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_history(
    batch_id: Optional[str] = None,
    recommend_level: Optional[str] = None,
    page: int = 1,
    page_size: int = 50,
) -> dict:
    """
    Query recommendation history with optional filters and pagination.

    Returns:
        dict with: total, page, page_size, items
    """
    db: Session = SessionLocal()
    try:
        query = db.query(Recommendation)

        if batch_id:
            query = query.filter(Recommendation.batch_id == batch_id)
        if recommend_level:
            query = query.filter(Recommendation.recommend_level == recommend_level)

        total = query.count()
        offset = (page - 1) * page_size
        records = (
            query.order_by(Recommendation.created_at.desc())
            .offset(offset)
            .limit(page_size)
            .all()
        )

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "items": [r.to_dict() for r in records],
        }
    finally:
        db.close()


def get_batches() -> list[dict]:
    """List all batch IDs with record counts and timestamps."""
    db: Session = SessionLocal()
    try:
        batches = (
            db.query(
                Recommendation.batch_id,
                func.count(Recommendation.id).label("count"),
                func.max(Recommendation.created_at).label("latest"),
            )
            .group_by(Recommendation.batch_id)
            .order_by(func.max(Recommendation.created_at).desc())
            .all()
        )

        return [
            {
                "batch_id": b.batch_id,
                "record_count": b.count,
                "latest_time": b.latest.isoformat() if b.latest else None,
            }
            for b in batches
        ]
    finally:
        db.close()


def export_csv(
    batch_id: Optional[str] = None,
    recommend_level: Optional[str] = None,
) -> tuple[str, io.StringIO]:
    """
    Export recommendations to CSV format.

    Returns:
        (filename, StringIO_buffer)
    """
    db: Session = SessionLocal()
    try:
        query = db.query(Recommendation)

        if batch_id:
            query = query.filter(Recommendation.batch_id == batch_id)
        if recommend_level:
            query = query.filter(Recommendation.recommend_level == recommend_level)

        records = query.order_by(Recommendation.id.asc()).all()

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["customer_id", "probability", "recommend_level", "reason", "batch_id", "created_at"])

        for r in records:
            writer.writerow([
                r.customer_id,
                f"{r.probability:.4f}",
                r.recommend_level,
                r.reason,
                r.batch_id,
                r.created_at.isoformat() if r.created_at else "",
            ])

        output.seek(0)
        filename = f"recommendations_{batch_id or 'all'}.csv"
        return filename, output
    finally:
        db.close()

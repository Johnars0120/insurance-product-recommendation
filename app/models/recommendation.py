"""Recommendation result model for storing prediction results."""

from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Recommendation(Base):
    __tablename__ = "recommendations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    customer_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    probability: Mapped[float] = mapped_column(Float, nullable=False)
    recommend_level: Mapped[str] = mapped_column(String(16), nullable=False)  # high / medium / low
    reason: Mapped[str] = mapped_column(String(256), nullable=False, default="")
    batch_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)  # 批次标识，同一次批量预测共享
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "customer_id": self.customer_id,
            "probability": self.probability,
            "recommend_level": self.recommend_level,
            "reason": self.reason,
            "batch_id": self.batch_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

"""Recommendation API routes: predict / history / export."""

from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.services import recommend_service

router = APIRouter(prefix="/api/recommend", tags=["recommend"])


# ---------- request / response schemas ----------

class PredictionInput(BaseModel):
    customer_id: str
    probability: float = Field(..., ge=0.0, le=1.0)
    recommend_level: Optional[str] = None
    reason: Optional[str] = None


class SaveRequest(BaseModel):
    predictions: list[PredictionInput]
    batch_id: Optional[str] = None


# ---------- endpoints ----------

@router.post("/predict")
def save_predictions(body: SaveRequest):
    """
    保存推荐预测结果到数据库。

    输入格式（来自算法同学预测结果）：
    [
        {"customer_id": "C001", "probability": 0.82, "recommend_level": "high", "reason": "..."},
        ...
    ]
    """
    if not body.predictions:
        raise HTTPException(status_code=400, detail="predictions list cannot be empty")

    payload = [p.model_dump() for p in body.predictions]
    result = recommend_service.save_results(payload, batch_id=body.batch_id)
    return result


@router.get("/history")
def get_history(
    batch_id: Optional[str] = Query(None, description="按批次 ID 筛选"),
    recommend_level: Optional[str] = Query(
        None, description="按推荐等级筛选: high / medium / low"
    ),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(50, ge=1, le=500, description="每页条数"),
):
    """分页查询推荐历史记录。"""
    return recommend_service.get_history(
        batch_id=batch_id,
        recommend_level=recommend_level,
        page=page,
        page_size=page_size,
    )


@router.get("/batches")
def get_batches():
    """获取所有批次列表（用于下拉选择）。"""
    return recommend_service.get_batches()


@router.get("/export")
def export_csv(
    batch_id: Optional[str] = Query(None, description="按批次导出，为空则导出全部"),
    recommend_level: Optional[str] = Query(None, description="按等级筛选"),
):
    """导出推荐结果为 CSV 文件下载。"""
    filename, buffer = recommend_service.export_csv(
        batch_id=batch_id,
        recommend_level=recommend_level,
    )
    return StreamingResponse(
        buffer,
        media_type="text/csv; charset=utf-8-sig",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )

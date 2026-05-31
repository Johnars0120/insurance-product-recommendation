from fastapi import APIRouter

from app.services.dataset_service import build_dataset_profile


router = APIRouter(prefix="/api/datasets", tags=["datasets"])


@router.get("/profile")
def get_dataset_profile():
    return build_dataset_profile()

import os

from fastapi import APIRouter, File, Header, HTTPException, UploadFile

from app.services.dataset_service import build_dataset_profile, save_uploaded_datasets


router = APIRouter(prefix="/api/datasets", tags=["datasets"])


@router.get("/profile")
def get_dataset_profile():
    return build_dataset_profile()


@router.post("/upload")
async def upload_datasets(
    train_file: UploadFile = File(...),
    eval_file: UploadFile = File(...),
    x_admin_token: str | None = Header(default=None),
):
    expected_token = os.getenv("INSURANCE_RECOMMENDATION_ADMIN_TOKEN")
    if expected_token and x_admin_token != expected_token:
        raise HTTPException(status_code=403, detail="Invalid admin token")

    try:
        profile = save_uploaded_datasets(
            train_bytes=await train_file.read(),
            train_filename=train_file.filename or "",
            eval_bytes=await eval_file.read(),
            eval_filename=eval_file.filename or "",
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "message": "Dataset files uploaded",
        "profile": profile,
    }

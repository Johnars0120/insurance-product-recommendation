from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

from app.config import BASE_DIR
from app.services.dataset_service import build_dataset_profile
from app.services.model_service import SUPPORTED_MODELS, get_latest_run


router = APIRouter(tags=["pages"])
templates = Jinja2Templates(directory=BASE_DIR / "app" / "templates")


@router.get("/", include_in_schema=False)
def home(request: Request):
    latest_run = get_latest_run()
    return templates.TemplateResponse(
        request,
        "home.html",
        {
            "active_page": "home",
            "latest_run": latest_run,
        },
    )


@router.get("/data", include_in_schema=False)
def data_page(request: Request):
    profile = build_dataset_profile()
    show_analysis = request.query_params.get("uploaded") == "1"
    return templates.TemplateResponse(
        request,
        "data.html",
        {
            "active_page": "data",
            "profile": profile,
            "show_analysis": show_analysis,
        },
    )


@router.get("/train", include_in_schema=False)
def train_page(request: Request):
    return templates.TemplateResponse(
        request,
        "train.html",
        {
            "active_page": "train",
            "available_models": list(SUPPORTED_MODELS),
            "latest_run": get_latest_run(),
        },
    )


@router.get("/evaluate", include_in_schema=False)
def evaluate_page(request: Request):
    return templates.TemplateResponse(
        request,
        "evaluate.html",
        {
            "active_page": "evaluate",
            "latest_run": get_latest_run(),
        },
    )


@router.get("/recommend", include_in_schema=False)
def recommend_page(request: Request):
    return templates.TemplateResponse(
        request,
        "recommend.html",
        {
            "active_page": "recommend",
        },
    )

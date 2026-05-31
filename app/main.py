from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.config import BASE_DIR
from app.routers import datasets, models, pages, recommendations


app = FastAPI(
    title="保险产品智能推荐系统",
    description="A lightweight FastAPI web system for insurance product recommendation.",
    version="0.1.0",
)

app.mount("/static", StaticFiles(directory=BASE_DIR / "app" / "static"), name="static")

app.include_router(datasets.router)
app.include_router(models.router)
app.include_router(recommendations.router)
app.include_router(pages.router)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "project": "insurance-product-recommendation",
    }

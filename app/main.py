import os

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.config import BASE_DIR
from app.database import configure_database, create_tables
from app.routers import datasets, models, pages, recommendations


app = FastAPI(
    title="保险产品智能推荐系统",
    description="A lightweight FastAPI web system for insurance product recommendation.",
    version="0.1.0",
)

database_url = os.getenv("INSURANCE_RECOMMENDATION_DATABASE_URL")
if database_url:
    configure_database(database_url)
create_tables()

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

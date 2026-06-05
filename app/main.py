from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import init_db
from app.routers import recommend


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create database tables on application startup."""
    init_db()
    yield


app = FastAPI(
    title="保险产品智能推荐系统",
    description="A lightweight FastAPI web system for insurance product recommendation.",
    version="0.1.0",
    lifespan=lifespan,
)

# 注册路由
app.include_router(recommend.router)


@app.get("/", include_in_schema=False)
def home():
    return {
        "message": "保险产品智能推荐系统",
        "health": "/health",
        "api_docs": "/docs",
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
        "project": "insurance-product-recommendation",
    }

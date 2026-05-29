from fastapi import FastAPI


app = FastAPI(
    title="保险产品智能推荐系统",
    description="A lightweight FastAPI web system for insurance product recommendation.",
    version="0.1.0",
)


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

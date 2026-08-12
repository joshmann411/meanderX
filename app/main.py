from fastapi import FastAPI
from app.config.settings import settings

app = FastAPI(title="MeanderX - Con Edison ArcGIS Foundation")


@app.get("/health")
async def health():
    return {"status": "healthy", "env": settings.app_env}

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
import logging

from app.api.v1.routes import router as api_v1_router
from app.config.settings import settings

logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO))

app = FastAPI(
    title="MeanderX Customer Query API",
    description="Domain-oriented API for querying Con Edison feeder and substation data ingested into PostGIS.",
    version="0.1.0",
)

app.include_router(api_v1_router)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    code = "not_found" if exc.status_code == 404 else "bad_request" if exc.status_code == 400 else "http_error"
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": code, "message": str(exc.detail)}},
    )


@app.get("/health")
async def health():
    return {"status": "healthy", "env": settings.app_env}

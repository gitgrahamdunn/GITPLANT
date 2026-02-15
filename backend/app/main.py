import time
import uuid

from fastapi import FastAPI, Request

from app.config import settings
from app.db import init_db
from app.routers import auth, documents, health

app = FastAPI(title=settings.app_name)
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(documents.router)


@app.middleware("http")
async def hardening_middleware(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = round((time.perf_counter() - start) * 1000, 2)
    response.headers["X-Process-Time-ms"] = str(duration_ms)
    return response


@app.on_event("startup")
def on_startup() -> None:
    pass


@app.get("/", tags=["root"])
def read_root():
    return {
        "name": settings.app_name,
        "environment": settings.app_env,
        "message": "EDMS backend is running",
    }

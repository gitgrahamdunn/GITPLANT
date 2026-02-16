import time
import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.db import init_db
from app.routers import auth, documents, health

app = FastAPI(title=settings.app_name)

# CORS (dev)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
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
    # If your init_db() creates tables and demo users, keep this.
    init_db()


@app.get("/", tags=["root"])
def read_root():
    return {
        "name": settings.app_name,
        "environment": settings.app_env,
        "message": "EDMS backend is running",
    }

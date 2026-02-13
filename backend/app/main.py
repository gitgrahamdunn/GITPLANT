from fastapi import FastAPI

from app.config import settings
from app.db import init_db
from app.routers import auth, health

app = FastAPI(title=settings.app_name)
app.include_router(health.router)
app.include_router(auth.router)


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.get("/", tags=["root"])
def read_root():
    return {
        "name": settings.app_name,
        "environment": settings.app_env,
        "message": "EDMS backend is running",
    }

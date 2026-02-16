from fastapi import APIRouter
from sqlmodel import Session, select

from app.config import (
    get_document_storage_path,
    resolve_sqlite_path,
    sanitize_database_url,
    settings,
)
from app.db import engine

router = APIRouter(prefix="/health", tags=["health"])


@router.get("", summary="Health check")
def health_check():
    return {"status": "ok"}


@router.get("/info", summary="Runtime environment and storage info")
def health_info():
    sqlite_path = resolve_sqlite_path(settings.database_url)
    return {
        "status": "ok",
        "database_url": sanitize_database_url(settings.database_url),
        "sqlite_path": str(sqlite_path) if sqlite_path else None,
        "document_storage_dir": str(get_document_storage_path()),
    }


@router.get("/live", summary="Liveness probe")
def liveness_probe():
    return {"status": "alive"}


@router.get("/ready", summary="Readiness probe")
def readiness_probe():
    try:
        with Session(engine) as session:
            session.exec(select(1)).one()
        return {"status": "ready"}
    except Exception:
        return {"status": "not_ready"}

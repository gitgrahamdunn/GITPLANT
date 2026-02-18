import os

from fastapi import APIRouter
from sqlmodel import Session, select

from app.config import (
    ensure_data_dir,
    get_data_dir,
    get_document_storage_path,
    get_storage_dir,
    get_working_storage_path,
    resolve_sqlite_path,
    sanitize_database_url,
    settings,
)
from app.db import engine

router = APIRouter(prefix="/health", tags=["health"])


@router.get("", summary="Health check")
def health_check():
    return {"status": "ok"}


def run_runtime_storage_check() -> dict:
    checks: dict[str, dict[str, str | bool]] = {}
    env_overrides = {
        "DATA_DIR": bool(os.getenv("DATA_DIR")),
        "STORAGE_DIR": bool(os.getenv("STORAGE_DIR")),
        "WORKING_STORAGE_DIR": bool(os.getenv("WORKING_STORAGE_DIR")),
    }

    for name, resolver in {
        "data_dir": ensure_data_dir,
        "document_storage_dir": get_document_storage_path,
        "storage_dir": get_storage_dir,
        "working_storage_dir": get_working_storage_path,
    }.items():
        path = resolver()
        path_str = str(path)
        checks[name] = {
            "path": path_str,
            "under_tmp": path_str.startswith("/tmp"),
            "exists": path.exists(),
            "writable": path.is_dir(),
        }

    checks["configured_data_dir"] = {
        "path": str(get_data_dir()),
        "under_tmp": str(get_data_dir()).startswith("/tmp"),
        "exists": True,
        "writable": True,
    }
    checks["env_overrides_present"] = {
        "path": ", ".join([key for key, enabled in env_overrides.items() if enabled]) or "none",
        "under_tmp": True,
        "exists": True,
        "writable": True,
    }
    return checks


@router.get("/info", summary="Runtime environment and storage info")
def health_info():
    sqlite_path = resolve_sqlite_path(settings.database_url)
    return {
        "status": "ok",
        "database_url": sanitize_database_url(settings.database_url),
        "sqlite_path": str(sqlite_path) if sqlite_path else None,
        "document_storage_dir": str(get_document_storage_path()),
        "storage_checks": run_runtime_storage_check(),
    }


@router.get("/storage", summary="Writable storage runtime check")
def storage_check():
    return {"status": "ok", "checks": run_runtime_storage_check()}


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

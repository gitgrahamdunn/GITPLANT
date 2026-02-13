from fastapi import APIRouter
from sqlmodel import Session, select

from app.db import engine

router = APIRouter(prefix="/health", tags=["health"])


@router.get("", summary="Health check")
def health_check():
    return {"status": "ok"}


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

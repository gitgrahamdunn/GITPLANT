from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, func, select

from app.config import settings
from app.db import get_session
from app.models import AuditEvent, Document, Project, ProjectWorkingRevision
from app.schemas import DemoSeedResponse
from app.security import CurrentUser, require_roles
from app.seed import seed_demo_data, wipe_all_data

router = APIRouter(prefix="/dev", tags=["dev"])


class UiAuditRequest(BaseModel):
    name: str
    payload: dict[str, object] | None = None


def _ensure_dev_enabled() -> None:
    if not settings.enable_demo_tools:
        raise HTTPException(status_code=403, detail="Dev endpoints disabled")


@router.post("/seed", response_model=DemoSeedResponse)
def seed_demo(
    session: Session = Depends(get_session),
    _: CurrentUser = Depends(require_roles("user")),
):
    _ensure_dev_enabled()
    wipe_all_data(session)
    return seed_demo_data(session)


@router.post("/reset", response_model=DemoSeedResponse)
def reset_demo(
    session: Session = Depends(get_session),
    _: CurrentUser = Depends(require_roles("user")),
):
    _ensure_dev_enabled()
    wipe_all_data(session)
    return DemoSeedResponse(
        status="ok",
        documents_created=0,
        approvals_created=0,
        audits_created=0,
        warning="Development-only endpoint. Do not enable in production.",
    )


@router.get("/status")
def dev_status(
    session: Session = Depends(get_session),
    _: CurrentUser = Depends(require_roles("user")),
):
    _ensure_dev_enabled()
    return {
        "documents": session.exec(select(func.count()).select_from(Document)).one(),
        "projects": session.exec(select(func.count()).select_from(Project)).one(),
        "working_revisions": session.exec(
            select(func.count()).select_from(ProjectWorkingRevision)
        ).one(),
        "audit_events": session.exec(select(func.count()).select_from(AuditEvent)).one(),
    }


@router.post("/audit/ui")
def audit_ui_event(
    payload: UiAuditRequest,
    user: CurrentUser = Depends(require_roles("user")),
):
    _ensure_dev_enabled()
    print(f"[ui-audit] user={user.email} event={payload.name} payload={payload.payload}")
    return {"status": "ok"}

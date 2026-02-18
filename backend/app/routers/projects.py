from datetime import datetime
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlmodel import Session, col, select

from app.config import BACKEND_ROOT
from app.db import get_session
from app.models import (
    AuditEvent,
    Branch,
    Document,
    DocumentRevision,
    Project,
    ProjectWorkingRevision,
)
from app.schemas import (
    ProjectCreateRequest,
    ProjectDetailResponse,
    ProjectMergeItemResponse,
    ProjectMergeResponse,
    ProjectPullRequest,
    ProjectPullResponse,
    ProjectSummaryResponse,
    ProjectWorkingRevisionResponse,
    ProjectWorkingUploadResponse,
    WorkingRevisionStatusResponse,
)
from app.security import CurrentUser, require_roles

router = APIRouter(prefix="/projects", tags=["projects"])

ACTIVE_WORKING_STATUSES = {"WORKING", "READY"}
WORKING_STORAGE_DIR = (BACKEND_ROOT / "storage" / "projects").resolve()


def ensure_working_storage_dir() -> None:
    WORKING_STORAGE_DIR.mkdir(parents=True, exist_ok=True)


def _to_working_response(
    row: ProjectWorkingRevision,
    document: Document,
) -> ProjectWorkingRevisionResponse:
    return ProjectWorkingRevisionResponse(
        id=row.id,
        project_id=row.project_id,
        document_id=row.document_id,
        document_number=document.document_number,
        title=document.title,
        current_plant_revision=document.current_revision,
        working_revision_label=row.working_revision_label,
        status=row.status,
        pulled_by=row.pulled_by,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _get_or_create_plant_branch(session: Session, document_id: int) -> Branch:
    branch = session.exec(
        select(Branch).where(Branch.document_id == document_id, Branch.name == "plant")
    ).first()
    if branch:
        return branch

    branch = Branch(document_id=document_id, name="plant")
    session.add(branch)
    session.commit()
    session.refresh(branch)
    return branch


def _next_revision(current_revision: str) -> str:
    cleaned = (current_revision or "A").strip().upper()
    if len(cleaned) == 1 and "A" <= cleaned <= "Y":
        return chr(ord(cleaned) + 1)
    if cleaned == "Z":
        return "AA"
    if cleaned == "AA":
        return "AB"
    if len(cleaned) == 2 and cleaned[0] == "A" and "A" <= cleaned[1] <= "Y":
        return f"A{chr(ord(cleaned[1]) + 1)}"
    return f"{cleaned}-NEXT"


def _resolve_project(session: Session, project_key: str) -> Project:
    project = session.exec(select(Project).where(Project.project_number == project_key)).first()
    if project:
        return project
    project = session.get(Project, project_key)
    if project:
        return project
    raise HTTPException(status_code=404, detail=f"Project not found for key: {project_key}")


def _get_project_by_id(session: Session, project_id: str) -> Project:
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Project not found for id: {project_id}")
    return project


@router.post("", response_model=ProjectSummaryResponse)
def create_project(
    payload: ProjectCreateRequest,
    session: Session = Depends(get_session),
    current_user: CurrentUser = Depends(require_roles("user")),
):
    existing = session.exec(
        select(Project).where(Project.project_number == payload.project_number)
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Project number already exists")

    project = Project(
        project_number=payload.project_number,
        name=payload.name,
        description=payload.description,
        created_by=current_user.email,
    )
    session.add(project)
    session.commit()
    session.refresh(project)

    return ProjectSummaryResponse(**project.model_dump(), working_doc_count=0)


@router.get("", response_model=list[ProjectSummaryResponse])
def list_projects(
    status: str | None = Query(default=None),
    session: Session = Depends(get_session),
    _: CurrentUser = Depends(require_roles("user")),
):
    query = select(Project)
    if status:
        normalized = status.upper()
        if normalized == "OPEN":
            normalized = "ACTIVE"
        query = query.where(Project.status == normalized)

    projects = session.exec(query.order_by(col(Project.created_at).desc())).all()
    responses: list[ProjectSummaryResponse] = []
    for project in projects:
        working_count = session.exec(
            select(ProjectWorkingRevision).where(
                ProjectWorkingRevision.project_id == project.id,
                ProjectWorkingRevision.status.in_(ACTIVE_WORKING_STATUSES),
            )
        ).all()
        responses.append(
            ProjectSummaryResponse(
                **project.model_dump(),
                working_doc_count=len(working_count),
            )
        )

    return responses


@router.get("/{project_number}", response_model=ProjectDetailResponse)
def get_project_detail(
    project_number: str,
    session: Session = Depends(get_session),
    _: CurrentUser = Depends(require_roles("user")),
):
    project = _resolve_project(session, project_number)

    working_rows = session.exec(
        select(ProjectWorkingRevision)
        .where(ProjectWorkingRevision.project_id == project.id)
        .order_by(col(ProjectWorkingRevision.created_at).desc())
    ).all()

    working_docs: list[ProjectWorkingRevisionResponse] = []
    for row in working_rows:
        document = session.get(Document, row.document_id)
        if not document:
            continue
        working_docs.append(_to_working_response(row, document))

    project_events = session.exec(
        select(AuditEvent)
        .where(AuditEvent.details.contains(project.project_number))
        .order_by(col(AuditEvent.created_at).desc())
    ).all()

    return ProjectDetailResponse(
        **project.model_dump(),
        working_docs=working_docs,
        events=project_events,
    )


@router.post("/{project_id}/pull", response_model=ProjectPullResponse)
def pull_documents_for_project(
    project_id: str,
    payload: ProjectPullRequest,
    session: Session = Depends(get_session),
    current_user: CurrentUser = Depends(require_roles("user")),
):
    project = _get_project_by_id(session, project_id)
    if project.status != "ACTIVE":
        raise HTTPException(status_code=409, detail="Only ACTIVE projects can pull")

    document_ids: set[int] = set()
    if payload.document_id is not None:
        document_ids.add(payload.document_id)
    if payload.document_ids:
        document_ids.update(payload.document_ids)

    if not document_ids:
        raise HTTPException(status_code=400, detail="No document_ids provided. Send document_ids: [int] or document_id: int")

    created: list[ProjectWorkingRevisionResponse] = []
    skipped: list[int] = []

    for document_id in sorted(document_ids):
        document = session.get(Document, document_id)
        if not document:
            skipped.append(document_id)
            continue

        existing = session.exec(
            select(ProjectWorkingRevision).where(
                ProjectWorkingRevision.project_id == project.id,
                ProjectWorkingRevision.document_id == document_id,
                ProjectWorkingRevision.status.in_(ACTIVE_WORKING_STATUSES),
            )
        ).first()
        if existing:
            skipped.append(document_id)
            continue

        latest_plant_revision = session.exec(
            select(DocumentRevision)
            .where(
                DocumentRevision.document_id == document_id,
                DocumentRevision.is_pushed.is_(True),
            )
            .order_by(col(DocumentRevision.id).desc())
        ).first()

        working = ProjectWorkingRevision(
            project_id=project.id,
            document_id=document_id,
            base_revision_id=(
                latest_plant_revision.id if latest_plant_revision else None
            ),
            working_revision_label=f"{document.current_revision}-W",
            status="WORKING",
            pulled_by=current_user.email,
        )
        session.add(working)
        session.commit()
        session.refresh(working)

        session.add(
            AuditEvent(
                document_id=document_id,
                event_type="project_pull",
                actor_email=current_user.email,
                details=f"Pulled into project {project.project_number} as working revision {working.id}",
            )
        )
        session.commit()
        created.append(_to_working_response(working, document))

    return ProjectPullResponse(
        project_number=project.project_number,
        created=created,
        skipped_document_ids=skipped,
    )


@router.post(
    "/{project_id}/working/{working_revision_id}/upload",
    response_model=ProjectWorkingUploadResponse,
)
def upload_working_revision_file(
    project_id: str,
    working_revision_id: int,
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
    current_user: CurrentUser = Depends(require_roles("user")),
):
    project = _get_project_by_id(session, project_id)
    working = session.get(ProjectWorkingRevision, working_revision_id)
    if not working or working.project_id != project.id:
        raise HTTPException(status_code=404, detail="Working revision not found for project")
    if working.status in {"MERGED", "ABANDONED"}:
        raise HTTPException(status_code=409, detail="Working revision is immutable")

    filename = (file.filename or "").lower()
    if not filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    ensure_working_storage_dir()
    destination = WORKING_STORAGE_DIR / f"{project.id}-{working.id}.pdf"
    file.file.seek(0)
    destination.write_bytes(file.file.read())

    working.file_path = str(destination)
    working.notes = f"Working upload by {current_user.email}"
    working.updated_at = datetime.utcnow()
    session.add(working)

    session.add(
        AuditEvent(
            document_id=working.document_id,
            event_type="project_working_upload",
            actor_email=current_user.email,
            details=f"Uploaded working revision file for {project.project_number} item {working.id}",
        )
    )
    session.commit()

    return ProjectWorkingUploadResponse(
        id=working.id,
        file_path=working.file_path,
        updated_at=working.updated_at,
    )


@router.post(
    "/{project_number}/working/{working_revision_id}/ready",
    response_model=WorkingRevisionStatusResponse,
)
def mark_working_ready(
    project_number: str,
    working_revision_id: int,
    session: Session = Depends(get_session),
    current_user: CurrentUser = Depends(require_roles("user")),
):
    project = _resolve_project(session, project_number)
    working = session.get(ProjectWorkingRevision, working_revision_id)
    if not working or working.project_id != project.id:
        raise HTTPException(
            status_code=404, detail="Working revision not found for project"
        )
    if working.status in {"MERGED", "ABANDONED"}:
        raise HTTPException(status_code=409, detail="Working revision is immutable")

    working.status = "READY"
    working.updated_at = datetime.utcnow()
    session.add(working)

    session.add(
        AuditEvent(
            document_id=working.document_id,
            event_type="project_ready",
            actor_email=current_user.email,
            details=f"Working revision {working.id} marked READY in {project.project_number}",
        )
    )
    session.commit()
    return WorkingRevisionStatusResponse(
        id=working.id,
        status=working.status,
        updated_at=working.updated_at,
    )


@router.post(
    "/{project_number}/working/{working_revision_id}/abandon",
    response_model=WorkingRevisionStatusResponse,
)
def abandon_working_revision(
    project_number: str,
    working_revision_id: int,
    session: Session = Depends(get_session),
    current_user: CurrentUser = Depends(require_roles("user")),
):
    project = _resolve_project(session, project_number)
    working = session.get(ProjectWorkingRevision, working_revision_id)
    if not working or working.project_id != project.id:
        raise HTTPException(
            status_code=404, detail="Working revision not found for project"
        )
    if working.status == "MERGED":
        raise HTTPException(
            status_code=409, detail="Merged working revision cannot be abandoned"
        )

    working.status = "ABANDONED"
    working.updated_at = datetime.utcnow()
    session.add(working)

    session.add(
        AuditEvent(
            document_id=working.document_id,
            event_type="project_abandoned",
            actor_email=current_user.email,
            details=f"Working revision {working.id} abandoned in {project.project_number}",
        )
    )
    session.commit()

    return WorkingRevisionStatusResponse(
        id=working.id,
        status=working.status,
        updated_at=working.updated_at,
    )


@router.post("/{project_number}/merge", response_model=ProjectMergeResponse)
def merge_project_to_plant(
    project_number: str,
    session: Session = Depends(get_session),
    current_user: CurrentUser = Depends(require_roles("user")),
):
    project = _resolve_project(session, project_number)
    ready_rows = session.exec(
        select(ProjectWorkingRevision).where(
            ProjectWorkingRevision.project_id == project.id,
            ProjectWorkingRevision.status == "READY",
        )
    ).all()

    merged_items: list[ProjectMergeItemResponse] = []

    for working in ready_rows:
        document = session.get(Document, working.document_id)
        if not document:
            continue

        previous_revision = document.current_revision
        next_revision = _next_revision(previous_revision)

        plant_branch = _get_or_create_plant_branch(session, document.id)
        plant_revision = DocumentRevision(
            document_id=document.id,
            branch_id=plant_branch.id,
            revision=next_revision,
            commit_message=f"Merged from project {project.project_number} working {working.id}",
            file_hash=f"project-merge-{project.project_number}-{working.id}-{int(datetime.utcnow().timestamp())}",
            author_email=current_user.email,
            content_text=working.notes,
            is_pushed=True,
        )
        session.add(plant_revision)
        session.commit()
        session.refresh(plant_revision)

        document.current_revision = next_revision
        session.add(document)

        working.status = "MERGED"
        working.merged_revision_id = plant_revision.id
        working.updated_at = datetime.utcnow()
        session.add(working)

        session.add(
            AuditEvent(
                document_id=document.id,
                event_type="project_merged",
                actor_email=current_user.email,
                details=f"Merged project {project.project_number} working {working.id} to plant revision {next_revision}",
            )
        )
        session.commit()

        merged_items.append(
            ProjectMergeItemResponse(
                working_revision_id=working.id,
                document_id=document.id,
                document_number=document.document_number,
                previous_revision=previous_revision,
                new_revision=next_revision,
            )
        )

    if merged_items:
        project.status = "MERGED"
        session.add(project)
        session.commit()

    return ProjectMergeResponse(
        project_number=project.project_number,
        merged_count=len(merged_items),
        merged_items=merged_items,
    )

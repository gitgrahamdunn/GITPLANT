import csv
import difflib
import json
from datetime import datetime
from io import StringIO
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile
from fastapi.responses import FileResponse
from sqlmodel import Session, col, delete, or_, select

from app.config import get_document_storage_path, settings
from app.db import get_session
from app.models import (
    Approval,
    AuditEvent,
    Branch,
    Document,
    DocumentRevision,
    Project,
    ProjectWorkingRevision,
    Transmittal,
)
from app.schemas import (
    ApprovalResponse,
    ApproveRequest,
    AuditEventResponse,
    BranchCreateRequest,
    BranchResponse,
    CommitRequest,
    CreateTransmittalRequest,
    DashboardExtendedResponse,
    DashboardSummaryResponse,
    DisciplineBreakdownItem,
    DocumentBatchCreateResponse,
    DocumentCreateRequest,
    DocumentResponse,
    DocumentSearchResponse,
    PullForRevisionResponse,
    PullResponse,
    PushResponse,
    RevisionCompareResponse,
    RevisionDiffField,
    RevisionResponse,
    StatusBreakdownItem,
    SubmitForApprovalRequest,
    TransmittalResponse,
    TextDiffResponse,
    BackupSnapshotResponse,
    DemoSeedResponse,
    RestoreSnapshotRequest,
)
from app.security import CurrentUser, get_current_user, require_roles

router = APIRouter(prefix="/documents", tags=["documents"])

DOCUMENT_STORAGE_DIR = get_document_storage_path(ensure_exists=False)


def record_audit_event(
    session: Session,
    document_id: int,
    event_type: str,
    actor_email: str,
    details: str,
) -> None:
    session.add(
        AuditEvent(
            document_id=document_id,
            event_type=event_type,
            actor_email=actor_email,
            details=details,
        )
    )


def _ensure_demo_tools_enabled() -> None:
    if not settings.demo_endpoints_enabled:
        raise HTTPException(
            status_code=403,
            detail="Demo tooling is disabled. Set ENABLE_DEMO_ENDPOINTS=true to use this endpoint.",
        )


def _clear_documents_and_storage(session: Session) -> None:
    session.exec(delete(AuditEvent))
    session.exec(delete(Transmittal))
    session.exec(delete(Approval))
    session.exec(delete(DocumentRevision))
    session.exec(delete(Branch))
    session.exec(delete(Document))
    session.commit()

    for path in get_document_storage_path(ensure_exists=False).glob("*.pdf"):
        path.unlink(missing_ok=True)


def _seed_demo_data(session: Session) -> DemoSeedResponse:
    demo_documents = [
        Document(
            project_code="PRJ-DEMO",
            document_number="CIV-1001",
            title="Site layout drawing",
            discipline="Civil",
            status="IFA",
            current_revision="B",
        ),
        Document(
            project_code="PRJ-DEMO",
            document_number="MECH-2201",
            title="Pump datasheet",
            discipline="Mechanical",
            status="IFC",
            current_revision="C",
        ),
        Document(
            project_code="PRJ-DEMO",
            document_number="ELEC-3104",
            title="Cable schedule",
            discipline="Electrical",
            status="WIP",
            current_revision="A",
        ),
    ]

    for document in demo_documents:
        session.add(document)
    session.commit()
    for document in demo_documents:
        session.refresh(document)

    branches: list[Branch] = []
    revisions: list[DocumentRevision] = []
    for idx, document in enumerate(demo_documents):
        branch = Branch(document_id=document.id, name="main")
        session.add(branch)
        session.commit()
        session.refresh(branch)
        branches.append(branch)

        revision = DocumentRevision(
            document_id=document.id,
            branch_id=branch.id,
            revision=document.current_revision,
            commit_message="Seeded demo revision",
            file_hash=f"demo-hash-{idx + 1}",
            author_email="user@edms.local",
            content_text="Demo seeded content",
            is_pushed=True,
        )
        session.add(revision)
        session.commit()
        session.refresh(revision)
        revisions.append(revision)

    approval = Approval(
        document_id=demo_documents[0].id,
        revision_id=revisions[0].id,
        approver_email="approver@edms.local",
        decision="approved",
        comments="Seeded approval for demo walkthrough",
        decided_at=datetime.utcnow(),
    )
    session.add(approval)

    session.add(
        AuditEvent(
            document_id=demo_documents[0].id,
            event_type="document_seeded",
            actor_email="system@seed.local",
            details="Demo document seeded with approval state",
        )
    )
    session.add(
        AuditEvent(
            document_id=demo_documents[1].id,
            event_type="transmittal_simulated",
            actor_email="system@seed.local",
            details="Demo transmittal event generated",
        )
    )
    session.commit()

    return DemoSeedResponse(
        status="ok",
        documents_created=len(demo_documents),
        approvals_created=1,
        audits_created=2,
        warning="Development-only endpoint. Do not enable in production.",
    )


def _active_project_counts_by_document(
    session: Session, document_ids: list[int]
) -> dict[int, int]:
    if not document_ids:
        return {}

    working_rows = session.exec(
        select(ProjectWorkingRevision, Project)
        .join(Project, Project.id == ProjectWorkingRevision.project_id)
        .where(
            ProjectWorkingRevision.document_id.in_(document_ids),
            ProjectWorkingRevision.status.in_(["WORKING", "READY"]),
            Project.status == "ACTIVE",
        )
    ).all()

    counts: dict[int, set[str]] = {}
    for working, project in working_rows:
        counts.setdefault(working.document_id, set()).add(project.id)

    return {doc_id: len(project_ids) for doc_id, project_ids in counts.items()}


def _to_document_response(
    document: Document, active_project_count: int = 0
) -> DocumentResponse:
    return DocumentResponse(
        id=document.id,
        project_code=document.project_code,
        document_number=document.document_number,
        title=document.title,
        discipline=document.discipline,
        status=document.status,
        current_revision=document.current_revision,
        file_path=document.file_path,
        active_project_count=active_project_count,
    )


def _deserialize_datetimes(row: dict, fields: list[str]) -> dict:
    parsed = dict(row)
    for field in fields:
        value = parsed.get(field)
        if isinstance(value, str):
            try:
                parsed[field] = datetime.fromisoformat(value)
            except ValueError:
                pass
    return parsed


@router.post("", response_model=DocumentResponse, summary="Create document")
def create_document(
    payload: DocumentCreateRequest,
    session: Session = Depends(get_session),
    current_user: CurrentUser = Depends(require_roles("user")),
):
    existing = session.exec(
        select(Document).where(Document.document_number == payload.document_number)
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Document number already exists")

    document = Document(**payload.model_dump())
    session.add(document)
    session.commit()
    session.refresh(document)

    record_audit_event(
        session,
        document.id,
        "document_created",
        current_user.email,
        f"Document {document.document_number} created",
    )
    session.commit()
    return _to_document_response(document)




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
def _document_pdf_path(document: Document) -> Path:
    if document.file_path:
        return Path(document.file_path)
    return DOCUMENT_STORAGE_DIR / f"{document.id}.pdf"


def _to_document_number(file_name: str, index: int) -> str:
    stem = file_name.rsplit(".", 1)[0].strip()
    normalized = "".join(ch if ch.isalnum() else "-" for ch in stem)
    normalized = "-".join(filter(None, normalized.split("-"))).upper()
    if not normalized:
        return f"PDF-{index + 1}"
    return normalized


@router.post(
    "/upload-pdf",
    response_model=DocumentBatchCreateResponse,
    summary="Create document records from uploaded PDF files",
)
def create_documents_from_pdf_upload(
    project_code: str = Form(...),
    discipline: str = Form(...),
    files: list[UploadFile] = File(...),
    session: Session = Depends(get_session),
    current_user: CurrentUser = Depends(require_roles("user")),
):
    created_documents: list[Document] = []

    for index, file in enumerate(files):
        file_name = (file.filename or "").strip()
        if not file_name.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")

        document_number = _to_document_number(file_name, index)
        existing = session.exec(
            select(Document).where(Document.document_number == document_number)
        ).first()
        if existing:
            raise HTTPException(
                status_code=409,
                detail=f"Document number already exists: {document_number}",
            )

        title = file_name.rsplit(".", 1)[0].strip() or "Untitled PDF document"
        document = Document(
            project_code=project_code,
            document_number=document_number,
            title=title,
            discipline=discipline,
        )
        session.add(document)
        session.commit()
        session.refresh(document)

        file.file.seek(0)
        destination = get_document_storage_path() / f"{document.id}.pdf"
        with destination.open("wb") as output_stream:
            output_stream.write(file.file.read())
        document.file_path = str(destination)
        session.add(document)

        record_audit_event(
            session,
            document.id,
            "document_created",
            current_user.email,
            f"Document {document.document_number} created from uploaded PDF {file_name}",
        )
        session.commit()
        created_documents.append(document)

    return DocumentBatchCreateResponse(
        total_created=len(created_documents), items=created_documents
    )




@router.post(
    "/{document_id}/plant/upload",
    response_model=DocumentResponse,
    summary="Upload new Plant revision PDF",
)
def upload_plant_revision(
    document_id: int,
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
    current_user: CurrentUser = Depends(require_roles("user")),
):
    document = session.get(Document, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    filename = (file.filename or "").lower()
    if not filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    next_revision = _next_revision(document.current_revision)
    destination = get_document_storage_path() / f"{document_id}.pdf"
    file.file.seek(0)
    destination.write_bytes(file.file.read())

    document.file_path = str(destination)

    plant_branch = _get_or_create_plant_branch(session, document_id)
    plant_revision = DocumentRevision(
        document_id=document.id,
        branch_id=plant_branch.id,
        revision=next_revision,
        commit_message=f"Plant upload from {current_user.email}",
        file_hash=f"plant-upload-{document.id}-{int(datetime.utcnow().timestamp())}",
        author_email=current_user.email,
        is_pushed=True,
    )
    session.add(plant_revision)

    document.current_revision = next_revision
    session.add(document)

    record_audit_event(
        session,
        document.id,
        "plant_upload",
        current_user.email,
        f"Uploaded new plant revision {next_revision} for {document.document_number}",
    )
    session.commit()

    return _to_document_response(document)

@router.post(
    "/{document_id}/pull-for-revision",
    response_model=PullForRevisionResponse,
    summary="Pull document file for revision",
)
def pull_document_for_revision(
    document_id: int,
    session: Session = Depends(get_session),
    current_user: CurrentUser = Depends(require_roles("user")),
):
    document = session.get(Document, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    pdf_path = _document_pdf_path(document)
    if not pdf_path.exists():
        raise HTTPException(
            status_code=404, detail="No PDF file found for this document"
        )

    record_audit_event(
        session,
        document_id,
        "document_pulled_for_revision",
        current_user.email,
        f"Document {document.document_number} pulled for revision",
    )
    session.commit()

    return PullForRevisionResponse(
        document_id=document_id,
        document_number=document.document_number,
        message="Document pulled for revision. You can now download and update the file.",
        download_url=f"/documents/{document_id}/download",
    )


@router.get(
    "/{document_id}/download",
    summary="Download latest document PDF",
)
def download_document_file(
    document_id: int,
    session: Session = Depends(get_session),
    current_user: CurrentUser = Depends(require_roles("user")),
):
    document = session.get(Document, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    pdf_path = _document_pdf_path(document)
    if not pdf_path.exists():
        raise HTTPException(
            status_code=404, detail="No PDF file found for this document"
        )

    record_audit_event(
        session,
        document_id,
        "document_downloaded",
        current_user.email,
        f"Document {document.document_number} downloaded",
    )
    session.commit()

    return FileResponse(
        path=str(pdf_path),
        media_type="application/pdf",
        filename=f"{document.document_number}.pdf",
    )


@router.get("", response_model=DocumentSearchResponse, summary="List documents")
def list_documents(
    session: Session = Depends(get_session),
    _: CurrentUser = Depends(require_roles("user")),
):
    items = session.exec(select(Document).order_by(col(Document.id))).all()
    counts = _active_project_counts_by_document(session, [item.id for item in items])
    result = [_to_document_response(item, counts.get(item.id, 0)) for item in items]
    return DocumentSearchResponse(total=len(result), items=result)


@router.get(
    "/search", response_model=DocumentSearchResponse, summary="Search documents"
)
def search_documents(
    session: Session = Depends(get_session),
    q: str | None = None,
    project_code: str | None = None,
    discipline: str | None = None,
    status: str | None = None,
):
    query = select(Document)

    if q:
        query = query.where(
            or_(
                Document.title.ilike(f"%{q}%"),
                Document.document_number.ilike(f"%{q}%"),
            )
        )
    if project_code:
        query = query.where(Document.project_code == project_code)
    if discipline:
        query = query.where(Document.discipline == discipline)
    if status:
        query = query.where(Document.status == status)

    items = session.exec(query.order_by(col(Document.id))).all()
    counts = _active_project_counts_by_document(session, [item.id for item in items])
    result = [_to_document_response(item, counts.get(item.id, 0)) for item in items]
    return DocumentSearchResponse(total=len(result), items=result)


@router.get(
    "/reports/dashboard-summary",
    response_model=DashboardSummaryResponse,
    summary="Dashboard metrics for document control",
)
def dashboard_summary(
    session: Session = Depends(get_session),
    _: CurrentUser = Depends(require_roles("user")),
):
    documents = session.exec(select(Document)).all()
    approvals = session.exec(select(Approval)).all()
    transmittals = session.exec(select(Transmittal)).all()

    return DashboardSummaryResponse(
        total_documents=len(documents),
        documents_ifa=sum(1 for d in documents if d.status == "IFA"),
        documents_ifc=sum(1 for d in documents if d.status == "IFC"),
        open_approvals=sum(1 for a in approvals if a.decision == "pending"),
        total_transmittals=len(transmittals),
    )


@router.get(
    "/reports/dashboard-extended",
    response_model=DashboardExtendedResponse,
    summary="Extended dashboard metrics",
)
def dashboard_extended(
    session: Session = Depends(get_session),
    _: CurrentUser = Depends(require_roles("user")),
):
    documents = session.exec(select(Document)).all()

    by_status: dict[str, int] = {}
    by_discipline: dict[str, int] = {}
    for doc in documents:
        by_status[doc.status] = by_status.get(doc.status, 0) + 1
        by_discipline[doc.discipline] = by_discipline.get(doc.discipline, 0) + 1

    status_breakdown = [
        StatusBreakdownItem(status=k, count=v)
        for k, v in sorted(by_status.items(), key=lambda item: item[0])
    ]
    discipline_breakdown = [
        DisciplineBreakdownItem(discipline=k, count=v)
        for k, v in sorted(by_discipline.items(), key=lambda item: item[0])
    ]

    return DashboardExtendedResponse(
        total_documents=len(documents),
        status_breakdown=status_breakdown,
        discipline_breakdown=discipline_breakdown,
    )


@router.post(
    "/{document_id}/branches", response_model=BranchResponse, summary="Create branch"
)
def create_branch(
    document_id: int,
    payload: BranchCreateRequest,
    session: Session = Depends(get_session),
    _: CurrentUser = Depends(require_roles("user")),
):
    document = session.get(Document, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    existing = session.exec(
        select(Branch).where(
            Branch.document_id == document_id, Branch.name == payload.name
        )
    ).first()
    if existing:
        raise HTTPException(
            status_code=409, detail="Branch already exists for this document"
        )

    branch = Branch(document_id=document_id, name=payload.name)
    session.add(branch)
    session.commit()
    session.refresh(branch)
    return branch


@router.post(
    "/{document_id}/commit", response_model=RevisionResponse, summary="Commit revision"
)
def commit_document_revision(
    document_id: int,
    payload: CommitRequest,
    branch: str,
    session: Session = Depends(get_session),
    current_user: CurrentUser = Depends(require_roles("user")),
):
    document = session.get(Document, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    branch_row = session.exec(
        select(Branch).where(Branch.document_id == document_id, Branch.name == branch)
    ).first()
    if not branch_row:
        raise HTTPException(status_code=404, detail="Branch not found")

    duplicate_revision = session.exec(
        select(DocumentRevision).where(
            DocumentRevision.document_id == document_id,
            DocumentRevision.branch_id == branch_row.id,
            DocumentRevision.revision == payload.revision,
        )
    ).first()
    if duplicate_revision:
        raise HTTPException(
            status_code=409, detail="Revision already exists on this branch"
        )

    revision = DocumentRevision(
        document_id=document_id,
        branch_id=branch_row.id,
        revision=payload.revision,
        commit_message=payload.commit_message,
        file_hash=payload.file_hash,
        author_email=str(payload.author_email),
        content_text=payload.content_text,
    )
    session.add(revision)
    session.commit()
    session.refresh(revision)

    record_audit_event(
        session,
        document_id,
        "revision_committed",
        current_user.email,
        f"Revision {payload.revision} committed on branch {branch}",
    )
    session.commit()
    return revision


@router.post(
    "/branches/{branch_id}/push", response_model=PushResponse, summary="Push revisions"
)
def push_branch(
    branch_id: int,
    session: Session = Depends(get_session),
    current_user: CurrentUser = Depends(require_roles("user")),
):
    branch = session.get(Branch, branch_id)
    if not branch:
        raise HTTPException(status_code=404, detail="Branch not found")

    pending_revisions = session.exec(
        select(DocumentRevision)
        .where(
            DocumentRevision.branch_id == branch_id,
            DocumentRevision.is_pushed.is_(False),
        )
        .order_by(col(DocumentRevision.id))
    ).all()

    if not pending_revisions:
        return PushResponse(branch_id=branch_id, pushed_count=0, latest_revision=None)

    for revision in pending_revisions:
        revision.is_pushed = True

    latest = pending_revisions[-1]
    document = session.get(Document, branch.document_id)
    if document:
        document.current_revision = latest.revision

    record_audit_event(
        session,
        branch.document_id,
        "branch_pushed",
        current_user.email,
        f"Pushed {len(pending_revisions)} revision(s) from branch {branch.name}",
    )
    session.commit()

    return PushResponse(
        branch_id=branch_id,
        pushed_count=len(pending_revisions),
        latest_revision=latest.revision,
    )


@router.post(
    "/branches/{branch_id}/pull",
    response_model=PullResponse,
    summary="Pull latest pushed revisions",
)
def pull_branch(branch_id: int, session: Session = Depends(get_session)):
    branch = session.get(Branch, branch_id)
    if not branch:
        raise HTTPException(status_code=404, detail="Branch not found")

    query = (
        select(DocumentRevision)
        .where(
            DocumentRevision.document_id == branch.document_id,
            DocumentRevision.is_pushed.is_(True),
        )
        .order_by(col(DocumentRevision.id))
    )

    if branch.latest_seen_revision_id is not None:
        query = query.where(DocumentRevision.id > branch.latest_seen_revision_id)

    updates = session.exec(query).all()

    if updates:
        branch.latest_seen_revision_id = updates[-1].id
        session.add(branch)
        session.commit()

    return PullResponse(branch_id=branch_id, updates=updates)


@router.get(
    "/{document_id}/compare",
    response_model=RevisionCompareResponse,
    summary="Compare two revisions",
)
def compare_document_revisions(
    document_id: int,
    from_revision_id: int,
    to_revision_id: int,
    session: Session = Depends(get_session),
):
    document = session.get(Document, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    from_revision = session.get(DocumentRevision, from_revision_id)
    to_revision = session.get(DocumentRevision, to_revision_id)

    if not from_revision or from_revision.document_id != document_id:
        raise HTTPException(
            status_code=404, detail="From revision not found for document"
        )
    if not to_revision or to_revision.document_id != document_id:
        raise HTTPException(
            status_code=404, detail="To revision not found for document"
        )

    fields_to_compare = [
        "revision",
        "commit_message",
        "file_hash",
        "author_email",
        "is_pushed",
    ]
    changed_fields: list[RevisionDiffField] = []

    for field in fields_to_compare:
        from_value = getattr(from_revision, field)
        to_value = getattr(to_revision, field)
        if from_value != to_value:
            changed_fields.append(
                RevisionDiffField(field=field, from_value=from_value, to_value=to_value)
            )

    return RevisionCompareResponse(
        document_id=document_id,
        from_revision=from_revision,
        to_revision=to_revision,
        changed_fields=changed_fields,
        is_same_file=from_revision.file_hash == to_revision.file_hash,
    )


@router.get(
    "/{document_id}/compare/text",
    response_model=TextDiffResponse,
    summary="Compare revision text content",
)
def compare_revision_text(
    document_id: int,
    from_revision_id: int,
    to_revision_id: int,
    session: Session = Depends(get_session),
):
    document = session.get(Document, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    from_revision = session.get(DocumentRevision, from_revision_id)
    to_revision = session.get(DocumentRevision, to_revision_id)
    if not from_revision or from_revision.document_id != document_id:
        raise HTTPException(
            status_code=404, detail="From revision not found for document"
        )
    if not to_revision or to_revision.document_id != document_id:
        raise HTTPException(
            status_code=404, detail="To revision not found for document"
        )

    from_lines = (from_revision.content_text or "").splitlines()
    to_lines = (to_revision.content_text or "").splitlines()
    diff = "\n".join(
        difflib.unified_diff(
            from_lines,
            to_lines,
            fromfile=f"rev-{from_revision.id}",
            tofile=f"rev-{to_revision.id}",
            lineterm="",
        )
    )

    return TextDiffResponse(
        document_id=document_id,
        from_revision_id=from_revision_id,
        to_revision_id=to_revision_id,
        diff=diff,
    )


@router.post(
    "/{document_id}/submit-for-approval",
    response_model=ApprovalResponse,
    summary="Submit a revision for approval",
)
def submit_for_approval(
    document_id: int,
    payload: SubmitForApprovalRequest,
    session: Session = Depends(get_session),
    current_user: CurrentUser = Depends(require_roles("user")),
):
    document = session.get(Document, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    revision = session.get(DocumentRevision, payload.revision_id)
    if not revision or revision.document_id != document_id:
        raise HTTPException(status_code=404, detail="Revision not found for document")

    if document.status not in {"WIP", "IFR", "IFI"}:
        raise HTTPException(
            status_code=409,
            detail=f"Document in status {document.status} cannot be submitted for approval",
        )

    document.status = "IFA"
    approval = Approval(
        document_id=document_id,
        revision_id=payload.revision_id,
        approver_email=str(payload.approver_email),
    )
    session.add(approval)
    record_audit_event(
        session,
        document_id,
        "submitted_for_approval",
        current_user.email,
        f"Revision {revision.revision} submitted to {payload.approver_email}",
    )
    session.commit()
    session.refresh(approval)
    return approval


@router.post(
    "/{document_id}/approvals/{approval_id}/decision",
    response_model=ApprovalResponse,
    summary="Approve or reject submitted revision",
)
def decide_approval(
    document_id: int,
    approval_id: int,
    payload: ApproveRequest,
    session: Session = Depends(get_session),
    current_user: CurrentUser = Depends(require_roles("user")),
):
    document = session.get(Document, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    approval = session.get(Approval, approval_id)
    if not approval or approval.document_id != document_id:
        raise HTTPException(
            status_code=404, detail="Approval request not found for document"
        )

    if approval.decision != "pending":
        raise HTTPException(
            status_code=409, detail="Approval decision already recorded"
        )

    approval.decision = payload.decision
    approval.comments = payload.comments
    approval.decided_at = datetime.utcnow()

    if payload.decision == "approved":
        document.status = "IFC"
    else:
        document.status = "IFR"

    session.add(approval)
    session.add(document)
    record_audit_event(
        session,
        document_id,
        "approval_decision",
        current_user.email,
        f"Decision: {payload.decision}",
    )
    session.commit()
    session.refresh(approval)
    return approval


@router.post(
    "/{document_id}/transmittals",
    response_model=TransmittalResponse,
    summary="Create transmittal for a revision",
)
def create_transmittal(
    document_id: int,
    payload: CreateTransmittalRequest,
    session: Session = Depends(get_session),
    current_user: CurrentUser = Depends(require_roles("user")),
):
    document = session.get(Document, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    revision = session.get(DocumentRevision, payload.revision_id)
    if not revision or revision.document_id != document_id:
        raise HTTPException(status_code=404, detail="Revision not found for document")

    exists = session.exec(
        select(Transmittal).where(
            Transmittal.transmittal_number == payload.transmittal_number
        )
    ).first()
    if exists:
        raise HTTPException(status_code=409, detail="Transmittal number already exists")

    transmittal = Transmittal(
        document_id=document_id,
        revision_id=payload.revision_id,
        transmittal_number=payload.transmittal_number,
        issued_to=payload.issued_to,
        vendor_code=payload.vendor_code,
        notes=payload.notes,
    )
    session.add(transmittal)
    record_audit_event(
        session,
        document_id,
        "transmittal_created",
        current_user.email,
        f"Transmittal {payload.transmittal_number} issued to {payload.issued_to}",
    )
    session.commit()
    session.refresh(transmittal)
    return transmittal


@router.get(
    "/{document_id}/transmittals",
    response_model=list[TransmittalResponse],
    summary="List document transmittals",
)
def list_transmittals(document_id: int, session: Session = Depends(get_session)):
    document = session.get(Document, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    return session.exec(
        select(Transmittal)
        .where(Transmittal.document_id == document_id)
        .order_by(col(Transmittal.id))
    ).all()


@router.get(
    "/{document_id}/audit-events",
    response_model=list[AuditEventResponse],
    summary="List audit events for a document",
)
def list_audit_events(document_id: int, session: Session = Depends(get_session)):
    document = session.get(Document, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    return session.exec(
        select(AuditEvent)
        .where(AuditEvent.document_id == document_id)
        .order_by(col(AuditEvent.id))
    ).all()


@router.get(
    "/{document_id}/audit-events/export",
    summary="Export audit events as CSV",
)
def export_audit_events_csv(
    document_id: int,
    session: Session = Depends(get_session),
    _: CurrentUser = Depends(require_roles("user")),
):
    document = session.get(Document, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    events = session.exec(
        select(AuditEvent)
        .where(AuditEvent.document_id == document_id)
        .order_by(col(AuditEvent.id))
    ).all()

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "event_type", "actor_email", "details", "created_at"])
    for event in events:
        writer.writerow(
            [
                event.id,
                event.event_type,
                event.actor_email,
                event.details,
                event.created_at,
            ]
        )

    filename = f"audit_document_{document_id}.csv"
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get(
    "/{document_id}/audit-events/export-jsonl",
    summary="Export audit events as JSON Lines",
)
def export_audit_events_jsonl(
    document_id: int,
    session: Session = Depends(get_session),
    _: CurrentUser = Depends(require_roles("user")),
):
    document = session.get(Document, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    events = session.exec(
        select(AuditEvent)
        .where(AuditEvent.document_id == document_id)
        .order_by(col(AuditEvent.id))
    ).all()

    lines = []
    for event in events:
        lines.append(
            json.dumps(
                {
                    "id": event.id,
                    "event_type": event.event_type,
                    "actor_email": event.actor_email,
                    "details": event.details,
                    "created_at": event.created_at.isoformat(),
                }
            )
        )

    filename = f"audit_document_{document_id}.jsonl"
    return Response(
        content="\n".join(lines),
        media_type="application/x-ndjson",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get(
    "/admin/backup",
    response_model=BackupSnapshotResponse,
    summary="Create full MVP backup snapshot",
)
def create_backup_snapshot(
    session: Session = Depends(get_session),
    _: CurrentUser = Depends(require_roles("user")),
):
    snapshot = {
        "documents": [
            d.model_dump(mode="json") for d in session.exec(select(Document)).all()
        ],
        "branches": [
            b.model_dump(mode="json") for b in session.exec(select(Branch)).all()
        ],
        "revisions": [
            r.model_dump(mode="json")
            for r in session.exec(select(DocumentRevision)).all()
        ],
        "approvals": [
            a.model_dump(mode="json") for a in session.exec(select(Approval)).all()
        ],
        "transmittals": [
            t.model_dump(mode="json") for t in session.exec(select(Transmittal)).all()
        ],
        "audit_events": [
            e.model_dump(mode="json") for e in session.exec(select(AuditEvent)).all()
        ],
    }
    return BackupSnapshotResponse(snapshot=snapshot)


@router.post(
    "/admin/restore",
    summary="Restore full MVP backup snapshot",
)
def restore_backup_snapshot(
    payload: RestoreSnapshotRequest,
    session: Session = Depends(get_session),
    _: CurrentUser = Depends(require_roles("user")),
):
    snapshot = payload.snapshot

    session.exec(delete(AuditEvent))
    session.exec(delete(Transmittal))
    session.exec(delete(Approval))
    session.exec(delete(DocumentRevision))
    session.exec(delete(Branch))
    session.exec(delete(Document))
    session.commit()

    for row in snapshot.get("documents", []):
        session.add(Document(**_deserialize_datetimes(row, ["created_at"])))
    for row in snapshot.get("branches", []):
        session.add(Branch(**_deserialize_datetimes(row, ["created_at"])))
    for row in snapshot.get("revisions", []):
        session.add(DocumentRevision(**_deserialize_datetimes(row, ["created_at"])))
    for row in snapshot.get("approvals", []):
        session.add(
            Approval(**_deserialize_datetimes(row, ["created_at", "decided_at"]))
        )
    for row in snapshot.get("transmittals", []):
        session.add(Transmittal(**_deserialize_datetimes(row, ["created_at"])))
    for row in snapshot.get("audit_events", []):
        session.add(AuditEvent(**_deserialize_datetimes(row, ["created_at"])))

    session.commit()
    return {"status": "restored"}


@router.post(
    "/admin/dev/seed-demo",
    response_model=DemoSeedResponse,
    summary="Seed development demo data",
)
def seed_demo_data(
    session: Session = Depends(get_session),
    _: CurrentUser = Depends(require_roles("user")),
):
    _ensure_demo_tools_enabled()
    return _seed_demo_data(session)


@router.post(
    "/admin/dev/reset-demo",
    response_model=DemoSeedResponse,
    summary="Reset and reseed development demo data",
)
def reset_demo_data(
    session: Session = Depends(get_session),
    _: CurrentUser = Depends(require_roles("user")),
):
    _ensure_demo_tools_enabled()
    _clear_documents_and_storage(session)
    return _seed_demo_data(session)


@router.get(
    "/{document_id}/history",
    response_model=list[RevisionResponse],
    summary="Revision history",
)
def get_document_history(document_id: int, session: Session = Depends(get_session)):
    document = session.get(Document, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    revisions = session.exec(
        select(DocumentRevision)
        .where(DocumentRevision.document_id == document_id)
        .order_by(col(DocumentRevision.id))
    ).all()
    return revisions

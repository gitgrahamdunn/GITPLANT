import csv
import difflib
import json
from datetime import datetime
from io import StringIO

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlmodel import Session, col, delete, or_, select

from app.db import get_session
from app.models import Approval, AuditEvent, Branch, Document, DocumentRevision, Transmittal
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
    DocumentCreateRequest,
    DocumentResponse,
    DocumentSearchResponse,
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
    RestoreSnapshotRequest,
)
from app.security import CurrentUser, get_current_user, require_roles

router = APIRouter(prefix="/documents", tags=["documents"])


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
    return document


@router.get("/search", response_model=DocumentSearchResponse, summary="Search documents")
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
    return DocumentSearchResponse(total=len(items), items=items)


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


@router.post("/{document_id}/branches", response_model=BranchResponse, summary="Create branch")
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
        select(Branch).where(Branch.document_id == document_id, Branch.name == payload.name)
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Branch already exists for this document")

    branch = Branch(document_id=document_id, name=payload.name)
    session.add(branch)
    session.commit()
    session.refresh(branch)
    return branch


@router.post("/{document_id}/commit", response_model=RevisionResponse, summary="Commit revision")
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
        raise HTTPException(status_code=409, detail="Revision already exists on this branch")

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


@router.post("/branches/{branch_id}/push", response_model=PushResponse, summary="Push revisions")
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
        .where(DocumentRevision.branch_id == branch_id, DocumentRevision.is_pushed.is_(False))
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


@router.post("/branches/{branch_id}/pull", response_model=PullResponse, summary="Pull latest pushed revisions")
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
        raise HTTPException(status_code=404, detail="From revision not found for document")
    if not to_revision or to_revision.document_id != document_id:
        raise HTTPException(status_code=404, detail="To revision not found for document")

    fields_to_compare = ["revision", "commit_message", "file_hash", "author_email", "is_pushed"]
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
        raise HTTPException(status_code=404, detail="From revision not found for document")
    if not to_revision or to_revision.document_id != document_id:
        raise HTTPException(status_code=404, detail="To revision not found for document")

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
        raise HTTPException(status_code=404, detail="Approval request not found for document")

    if approval.decision != "pending":
        raise HTTPException(status_code=409, detail="Approval decision already recorded")

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
        select(Transmittal).where(Transmittal.transmittal_number == payload.transmittal_number)
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
        writer.writerow([event.id, event.event_type, event.actor_email, event.details, event.created_at])

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
        "documents": [d.model_dump(mode="json") for d in session.exec(select(Document)).all()],
        "branches": [b.model_dump(mode="json") for b in session.exec(select(Branch)).all()],
        "revisions": [r.model_dump(mode="json") for r in session.exec(select(DocumentRevision)).all()],
        "approvals": [a.model_dump(mode="json") for a in session.exec(select(Approval)).all()],
        "transmittals": [t.model_dump(mode="json") for t in session.exec(select(Transmittal)).all()],
        "audit_events": [e.model_dump(mode="json") for e in session.exec(select(AuditEvent)).all()],
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
        session.add(Approval(**_deserialize_datetimes(row, ["created_at", "decided_at"])))
    for row in snapshot.get("transmittals", []):
        session.add(Transmittal(**_deserialize_datetimes(row, ["created_at"])))
    for row in snapshot.get("audit_events", []):
        session.add(AuditEvent(**_deserialize_datetimes(row, ["created_at"])))

    session.commit()
    return {"status": "restored"}

@router.get("/{document_id}/history", response_model=list[RevisionResponse], summary="Revision history")
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

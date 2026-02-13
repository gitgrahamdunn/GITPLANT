from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, col, select

from app.db import get_session
from app.models import Approval, Branch, Document, DocumentRevision
from app.schemas import (
    ApprovalResponse,
    ApproveRequest,
    BranchCreateRequest,
    BranchResponse,
    CommitRequest,
    DocumentCreateRequest,
    DocumentResponse,
    PullResponse,
    PushResponse,
    RevisionCompareResponse,
    RevisionDiffField,
    RevisionResponse,
    SubmitForApprovalRequest,
)

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("", response_model=DocumentResponse, summary="Create document")
def create_document(payload: DocumentCreateRequest, session: Session = Depends(get_session)):
    existing = session.exec(
        select(Document).where(Document.document_number == payload.document_number)
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Document number already exists")

    document = Document(**payload.model_dump())
    session.add(document)
    session.commit()
    session.refresh(document)
    return document


@router.post("/{document_id}/branches", response_model=BranchResponse, summary="Create branch")
def create_branch(
    document_id: int, payload: BranchCreateRequest, session: Session = Depends(get_session)
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
    document_id: int, payload: CommitRequest, branch: str, session: Session = Depends(get_session)
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
    )
    session.add(revision)
    session.commit()
    session.refresh(revision)
    return revision


@router.post("/branches/{branch_id}/push", response_model=PushResponse, summary="Push revisions")
def push_branch(branch_id: int, session: Session = Depends(get_session)):
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


@router.post(
    "/{document_id}/submit-for-approval",
    response_model=ApprovalResponse,
    summary="Submit a revision for approval",
)
def submit_for_approval(
    document_id: int,
    payload: SubmitForApprovalRequest,
    session: Session = Depends(get_session),
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
    session.commit()
    session.refresh(approval)
    return approval


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

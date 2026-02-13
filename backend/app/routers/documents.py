from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, col, select

from app.db import get_session
from app.models import Branch, Document, DocumentRevision
from app.schemas import (
    BranchCreateRequest,
    BranchResponse,
    CommitRequest,
    DocumentCreateRequest,
    DocumentResponse,
    PullResponse,
    PushResponse,
    RevisionResponse,
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

    session.add(branch)
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

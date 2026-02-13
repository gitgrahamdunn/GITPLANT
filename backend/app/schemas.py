from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, EmailStr


class AuthLoginRequest(BaseModel):
    email: EmailStr
    password: str


class AuthLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str


class DocumentCreateRequest(BaseModel):
    project_code: str
    document_number: str
    title: str
    discipline: str


class DocumentResponse(BaseModel):
    id: int
    project_code: str
    document_number: str
    title: str
    discipline: str
    status: str
    current_revision: str


class BranchCreateRequest(BaseModel):
    name: str


class BranchResponse(BaseModel):
    id: int
    document_id: int
    name: str


class CommitRequest(BaseModel):
    revision: str
    commit_message: str
    file_hash: str
    author_email: EmailStr


class RevisionResponse(BaseModel):
    id: int
    document_id: int
    branch_id: int
    revision: str
    commit_message: str
    file_hash: str
    author_email: str
    is_pushed: bool
    created_at: datetime


class PushResponse(BaseModel):
    branch_id: int
    pushed_count: int
    latest_revision: str | None


class PullResponse(BaseModel):
    branch_id: int
    updates: list[RevisionResponse]


class RevisionDiffField(BaseModel):
    field: str
    from_value: Any
    to_value: Any


class RevisionCompareResponse(BaseModel):
    document_id: int
    from_revision: RevisionResponse
    to_revision: RevisionResponse
    changed_fields: list[RevisionDiffField]
    is_same_file: bool


class SubmitForApprovalRequest(BaseModel):
    revision_id: int
    approver_email: EmailStr


class ApproveRequest(BaseModel):
    decision: Literal["approved", "rejected"]
    comments: str | None = None


class ApprovalResponse(BaseModel):
    id: int
    document_id: int
    revision_id: int
    approver_email: str
    decision: str
    comments: str | None
    decided_at: datetime | None
    created_at: datetime

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict


class ORMResponseModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class AuthLoginRequest(BaseModel):
    email: str
    password: str


class AuthLoginResponse(ORMResponseModel):
    access_token: str
    token_type: str = "bearer"
    role: str


class AuthMeResponse(ORMResponseModel):
    email: str
    role: str


class DocumentCreateRequest(BaseModel):
    project_code: str
    document_number: str
    title: str
    discipline: str


class DocumentResponse(ORMResponseModel):
    id: int
    project_code: str
    document_number: str
    title: str
    discipline: str
    status: str
    current_revision: str


class BranchCreateRequest(BaseModel):
    name: str


class BranchResponse(ORMResponseModel):
    id: int
    document_id: int
    name: str


class CommitRequest(BaseModel):
    revision: str
    commit_message: str
    file_hash: str
    author_email: str
    content_text: str | None = None


class RevisionResponse(ORMResponseModel):
    id: int
    document_id: int
    branch_id: int
    revision: str
    commit_message: str
    file_hash: str
    author_email: str
    content_text: str | None
    is_pushed: bool
    created_at: datetime


class PushResponse(ORMResponseModel):
    branch_id: int
    pushed_count: int
    latest_revision: str | None


class PullResponse(ORMResponseModel):
    branch_id: int
    updates: list[RevisionResponse]


class RevisionDiffField(ORMResponseModel):
    field: str
    from_value: Any
    to_value: Any


class RevisionCompareResponse(ORMResponseModel):
    document_id: int
    from_revision: RevisionResponse
    to_revision: RevisionResponse
    changed_fields: list[RevisionDiffField]
    is_same_file: bool


class SubmitForApprovalRequest(BaseModel):
    revision_id: int
    approver_email: str


class ApproveRequest(BaseModel):
    decision: Literal["approved", "rejected"]
    comments: str | None = None


class ApprovalResponse(ORMResponseModel):
    id: int
    document_id: int
    revision_id: int
    approver_email: str
    decision: str
    comments: str | None
    decided_at: datetime | None
    created_at: datetime


class DocumentSearchResponse(ORMResponseModel):
    total: int
    items: list[DocumentResponse]


class CreateTransmittalRequest(BaseModel):
    revision_id: int
    transmittal_number: str
    issued_to: str
    vendor_code: str
    notes: str | None = None


class TransmittalResponse(ORMResponseModel):
    id: int
    document_id: int
    revision_id: int
    transmittal_number: str
    issued_to: str
    vendor_code: str
    notes: str | None
    created_at: datetime


class AuditEventResponse(ORMResponseModel):
    id: int
    document_id: int
    event_type: str
    actor_email: str
    details: str
    created_at: datetime


class DashboardSummaryResponse(ORMResponseModel):
    total_documents: int
    documents_ifa: int
    documents_ifc: int
    open_approvals: int
    total_transmittals: int


class StatusBreakdownItem(ORMResponseModel):
    status: str
    count: int


class DisciplineBreakdownItem(ORMResponseModel):
    discipline: str
    count: int


class DashboardExtendedResponse(ORMResponseModel):
    total_documents: int
    status_breakdown: list[StatusBreakdownItem]
    discipline_breakdown: list[DisciplineBreakdownItem]


class TextDiffResponse(ORMResponseModel):
    document_id: int
    from_revision_id: int
    to_revision_id: int
    diff: str


class BackupSnapshotResponse(ORMResponseModel):
    snapshot: dict[str, list[dict[str, Any]]]


class RestoreSnapshotRequest(BaseModel):
    snapshot: dict[str, list[dict[str, Any]]]

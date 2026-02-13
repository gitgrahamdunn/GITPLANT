from datetime import datetime

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

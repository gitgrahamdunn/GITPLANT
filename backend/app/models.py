from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True)
    full_name: str
    role: str = Field(default="viewer", index=True)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Document(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    project_code: str = Field(index=True)
    document_number: str = Field(index=True, unique=True)
    title: str
    discipline: str = Field(index=True)
    status: str = Field(default="WIP", index=True)
    current_revision: str = Field(default="A")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Branch(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    document_id: int = Field(foreign_key="document.id", index=True)
    name: str = Field(index=True)
    latest_seen_revision_id: Optional[int] = Field(default=None, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class DocumentRevision(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    document_id: int = Field(foreign_key="document.id", index=True)
    branch_id: int = Field(foreign_key="branch.id", index=True)
    revision: str = Field(index=True)
    commit_message: str
    file_hash: str = Field(index=True)
    author_email: str
    is_pushed: bool = Field(default=False, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Approval(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    document_id: int = Field(foreign_key="document.id", index=True)
    revision_id: int = Field(foreign_key="documentrevision.id", index=True)
    approver_email: str = Field(index=True)
    decision: str = Field(default="pending", index=True)
    comments: Optional[str] = None
    decided_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Transmittal(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    document_id: int = Field(foreign_key="document.id", index=True)
    revision_id: int = Field(foreign_key="documentrevision.id", index=True)
    transmittal_number: str = Field(index=True, unique=True)
    issued_to: str = Field(index=True)
    vendor_code: str = Field(index=True)
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

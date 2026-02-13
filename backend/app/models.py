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


class DocumentRevision(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    document_id: int = Field(foreign_key="document.id", index=True)
    revision: str = Field(index=True)
    commit_message: str
    file_hash: str = Field(index=True)
    author_email: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

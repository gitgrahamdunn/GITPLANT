from fastapi.testclient import TestClient
from sqlmodel import Session, delete

from app.db import engine
from app.main import app
from app.models import Branch, Document, DocumentRevision

client = TestClient(app)


def reset_db() -> None:
    with Session(engine) as session:
        session.exec(delete(DocumentRevision))
        session.exec(delete(Branch))
        session.exec(delete(Document))
        session.commit()


def test_commit_push_pull_and_history_flow():
    reset_db()

    doc = client.post(
        "/documents",
        json={
            "project_code": "PRJ-1",
            "document_number": "P-1001",
            "title": "Compressor P&ID",
            "discipline": "Process",
        },
    )
    assert doc.status_code == 200
    document_id = doc.json()["id"]

    main_branch = client.post(f"/documents/{document_id}/branches", json={"name": "main"})
    assert main_branch.status_code == 200
    main_branch_id = main_branch.json()["id"]

    moc_branch = client.post(f"/documents/{document_id}/branches", json={"name": "moc-2026-014"})
    assert moc_branch.status_code == 200
    moc_branch_id = moc_branch.json()["id"]

    commit = client.post(
        f"/documents/{document_id}/commit?branch=moc-2026-014",
        json={
            "revision": "B",
            "commit_message": "Updated PSV sizing basis",
            "file_hash": "hash-b",
            "author_email": "engineer@edms.local",
        },
    )
    assert commit.status_code == 200
    assert commit.json()["is_pushed"] is False

    push = client.post(f"/documents/branches/{moc_branch_id}/push")
    assert push.status_code == 200
    assert push.json()["pushed_count"] == 1
    assert push.json()["latest_revision"] == "B"

    pull = client.post(f"/documents/branches/{main_branch_id}/pull")
    assert pull.status_code == 200
    assert len(pull.json()["updates"]) == 1
    assert pull.json()["updates"][0]["revision"] == "B"

    history = client.get(f"/documents/{document_id}/history")
    assert history.status_code == 200
    assert len(history.json()) == 1
    assert history.json()[0]["commit_message"] == "Updated PSV sizing basis"

from __future__ import annotations

from datetime import datetime, timedelta
from random import Random

from sqlmodel import Session, delete

from app.config import get_plant_storage_path
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
from app.schemas import DemoSeedResponse

DISCIPLINES = ["Civil", "Mechanical", "Electrical", "Process", "Piping", "Instrument"]
DOC_TITLES = [
    "General Arrangement",
    "Cable Schedule",
    "Isometric",
    "Control Philosophy",
    "Data Sheet",
    "Loop Diagram",
    "P&ID",
    "Hook-up Drawing",
]


def _write_placeholder_pdf(path, title: str) -> None:
    content = (
        "%PDF-1.1\n"
        "1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n"
        "2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n"
        "3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 300 144] /Contents 4 0 R >> endobj\n"
        f"4 0 obj << /Length {len(title) + 40} >> stream\nBT /F1 12 Tf 20 100 Td ({title}) Tj ET\nendstream endobj\n"
        "xref\n0 5\n0000000000 65535 f \n"
        "trailer << /Size 5 /Root 1 0 R >>\nstartxref\n0\n%%EOF\n"
    )
    path.write_bytes(content.encode("latin-1", errors="ignore"))


def wipe_all_data(session: Session) -> None:
    session.exec(delete(ProjectWorkingRevision))
    session.exec(delete(Project))
    session.exec(delete(AuditEvent))
    session.exec(delete(Transmittal))
    session.exec(delete(Approval))
    session.exec(delete(DocumentRevision))
    session.exec(delete(Branch))
    session.exec(delete(Document))
    session.commit()

    plant_storage = get_plant_storage_path()
    for pdf in plant_storage.glob("*.pdf"):
        pdf.unlink(missing_ok=True)


def _doc_number(idx: int) -> str:
    return f"DOC-{idx:03d}"


def seed_demo_data(session: Session, doc_count: int = 30, project_count: int = 8) -> DemoSeedResponse:
    rng = Random(42)
    now = datetime.utcnow()
    plant_storage = get_plant_storage_path()

    documents: list[Document] = []
    approvals_created = 0
    audits_created = 0

    for idx in range(1, doc_count + 1):
        discipline = DISCIPLINES[idx % len(DISCIPLINES)]
        title = f"{DOC_TITLES[idx % len(DOC_TITLES)]} {idx}"
        pdf_path = plant_storage / f"DOC-{idx:03d}.pdf"
        _write_placeholder_pdf(pdf_path, f"{_doc_number(idx)} - {title}")
        document = Document(
            project_code=f"PLT-{(idx % 4) + 1:02d}",
            document_number=_doc_number(idx),
            title=title,
            discipline=discipline,
            status=rng.choice(["IFA", "IFC", "WIP"]),
            current_revision=rng.choice(["A", "B", "C"]),
            file_path=str(pdf_path),
        )
        session.add(document)
        session.commit()
        session.refresh(document)
        documents.append(document)

        branch = Branch(document_id=document.id, name="plant")
        session.add(branch)
        session.commit()
        session.refresh(branch)

        revision = DocumentRevision(
            document_id=document.id,
            branch_id=branch.id,
            revision=document.current_revision,
            commit_message="Demo seeded plant revision",
            file_hash=f"demo-seed-{document.id}",
            author_email="system@seed.local",
            content_text=f"Placeholder content for {document.document_number}",
            is_pushed=True,
        )
        session.add(revision)
        session.commit()
        session.refresh(revision)

        if idx % 5 == 0:
            session.add(
                Approval(
                    document_id=document.id,
                    revision_id=revision.id,
                    approver_email="approver@edms.local",
                    decision="approved",
                    comments="Demo seeded approval",
                    decided_at=now - timedelta(days=idx),
                )
            )
            approvals_created += 1

        session.add(
            AuditEvent(
                document_id=document.id,
                event_type="document_seeded",
                actor_email="system@seed.local",
                details=f"Created demo document {document.document_number}",
            )
        )
        audits_created += 1
        session.commit()

    projects: list[Project] = []
    statuses = ["ACTIVE", "MERGED", "CLOSED", "ACTIVE", "ACTIVE", "MERGED", "CLOSED", "ACTIVE"]
    for idx in range(1, project_count + 1):
        project = Project(
            project_number=f"PRJ-{1000 + idx}",
            name=f"Demo Project {idx}",
            description=f"Workflow demo project {idx}",
            status=statuses[(idx - 1) % len(statuses)],
            created_by="user@edms.local",
            created_at=now - timedelta(days=project_count - idx),
        )
        session.add(project)
        session.commit()
        session.refresh(project)
        projects.append(project)

    for pidx, project in enumerate(projects):
        doc_slice = documents[pidx * 3 : pidx * 3 + 4]
        for didx, document in enumerate(doc_slice):
            status = "READY" if project.status == "ACTIVE" and didx % 2 == 0 else "WORKING"
            if project.status in {"MERGED", "CLOSED"}:
                status = "MERGED" if project.status == "MERGED" else "ABANDONED"
            working = ProjectWorkingRevision(
                project_id=project.id,
                document_id=document.id,
                working_revision_label=f"{document.current_revision}-W",
                status=status,
                pulled_by="user@edms.local",
                notes="Demo working revision",
                file_path=document.file_path,
                created_at=now - timedelta(days=10 - pidx),
                updated_at=now - timedelta(days=5 - didx),
            )
            session.add(working)
            session.commit()

            session.add(
                AuditEvent(
                    document_id=document.id,
                    event_type="project_event",
                    actor_email="user@edms.local",
                    details=f"{project.project_number}: pulled {document.document_number} as {status}",
                    created_at=now - timedelta(hours=pidx + didx),
                )
            )
            audits_created += 1

    session.commit()

    return DemoSeedResponse(
        status="ok",
        documents_created=len(documents),
        approvals_created=approvals_created,
        audits_created=audits_created,
        warning="Development-only endpoint. Do not enable in production.",
    )

from __future__ import annotations

from datetime import datetime, timedelta
from random import Random

from sqlmodel import Session, delete

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


def _doc_number(idx: int, discipline: str) -> str:
    prefix = discipline[:3].upper()
    return f"{prefix}-{1000 + idx:04d}"


def seed_demo_data(session: Session, doc_count: int = 30, project_count: int = 6) -> DemoSeedResponse:
    rng = Random(42)
    now = datetime.utcnow()

    documents: list[Document] = []
    approvals_created = 0
    audits_created = 0

    for idx in range(1, doc_count + 1):
      discipline = DISCIPLINES[idx % len(DISCIPLINES)]
      title = f"{DOC_TITLES[idx % len(DOC_TITLES)]} {idx}"
      document = Document(
          project_code=f"PLT-{(idx % 4) + 1:02d}",
          document_number=_doc_number(idx, discipline),
          title=title,
          discipline=discipline,
          status=rng.choice(["IFA", "IFC", "WIP"]),
          current_revision=rng.choice(["A", "B", "C"]),
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
    statuses = ["ACTIVE", "MERGED", "CLOSED", "ACTIVE", "ACTIVE", "MERGED"]
    for idx in range(1, project_count + 1):
      project = Project(
          project_number=f"PRJ-{120 + idx}",
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
            created_at=now - timedelta(days=10 - pidx),
            updated_at=now - timedelta(days=5 - didx),
        )
        session.add(working)
        session.commit()
        session.refresh(working)

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

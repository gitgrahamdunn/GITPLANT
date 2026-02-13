# Fast EDMS for Oil & Gas — Beginner Blueprint

## 1) What you are building
An **Engineering Document Management System (EDMS)** that:
- stores technical documents (P&IDs, datasheets, procedures, drawings, MOCs),
- tracks every revision,
- supports workflow (review, approval, issue for construction/operation),
- uses familiar **Git-like commands** (`commit`, `push`, `pull`) with audit history.

---

## 2) Core product idea (Git language for documents)
Use Git words, but adapt them for business users:

- `commit`: save a new version with a message ("Updated line list for compressor C-101").
- `push`: submit local changes to the central project vault.
- `pull`: fetch latest approved changes from the vault.
- `branch`: create a parallel revision stream (e.g., "MOC-2026-014").
- `merge`: combine reviewed branch updates into mainline documents.
- `tag`: mark milestones ("IFC", "As-Built", "Turnover Package").

This gives engineers version-control behavior without requiring actual Git commands in terminal.

---

## 3) Oil & gas-specific requirements (must-have)
1. **Document metadata model**
   - Project, Facility, Unit, Discipline, Doc Type, Doc Number, Revision, Status.
   - Vendor/Company codes and transmittal number.

2. **Revision & status control**
   - Statuses like WIP, IFA, IFR, IFI, IFC, As-Built.
   - Controlled transitions (e.g., IFC only after approval workflow).

3. **Review/approval workflow**
   - Sequential or parallel reviewers.
   - Electronic signatures and timestamps.

4. **Audit trail (regulatory)**
   - Who changed what, when, why, and which file hash.
   - Immutable event log.

5. **Access control**
   - Role-based access (Document Controller, Engineer, Approver, Contractor, Viewer).
   - Project and discipline-level permissions.

6. **Search and speed**
   - Full-text + metadata search.
   - Fast version retrieval for large PDF/CAD packages.

---

## 4) Suggested architecture (fast and scalable)
- **Frontend**: React + TypeScript.
- **Backend API**: FastAPI (Python) or NestJS (Node).
- **Database**: PostgreSQL (metadata + revision graph).
- **Object storage**: S3-compatible store (MinIO/AWS S3) for binary files.
- **Search**: OpenSearch/Elasticsearch for metadata + content indexing.
- **Cache/queue**: Redis + background workers (Celery/BullMQ).
- **Auth**: OIDC/SAML (enterprise SSO-ready).

### Key performance design choices
- Store large files in object storage, not database blobs.
- Use content hashing (SHA-256) to deduplicate identical files.
- Precompute revision timelines and metadata indexes.
- Async processing for OCR, text extraction, thumbnail generation.

---

## 5) Domain model (simple v1)
Main entities:
- `Document` (logical identity across revisions)
- `DocumentRevision` (one saved version / commit)
- `Branch` (parallel workstream)
- `MergeRequest` (review + approval to merge)
- `Transmittal` (batch issue to contractor/vendor)
- `User`, `Role`, `Permission`
- `AuditEvent`

---

## 6) API sketch using Git-like actions
- `POST /documents/{id}/commit`
- `POST /branches/{branchId}/push`
- `POST /branches/{branchId}/pull`
- `POST /merge-requests`
- `POST /merge-requests/{id}/approve`
- `POST /merge-requests/{id}/merge`
- `GET /documents/{id}/history`

Tip: keep UI labels business-friendly ("Submit", "Sync", "Review") and show Git words as advanced hints.

---

## 7) 12-week MVP roadmap
### Weeks 1–2: Foundations
- Project setup, auth, user roles.
- Data model for documents/revisions/metadata.

### Weeks 3–4: Versioning core
- Commit, pull, push operations.
- Revision history and comparison (metadata + file diff where possible).

### Weeks 5–6: Workflow
- Review/approval flows.
- Status transitions and validation rules.

### Weeks 7–8: Search + performance
- Metadata and full-text indexing.
- Caching and pagination for large repositories.

### Weeks 9–10: Oil & gas controls
- Transmittals, discipline filters, document numbering templates.
- Audit log export.

### Weeks 11–12: Hardening
- Security tests, backup/restore drill.
- Pilot with one project team.

---

## 8) Team for first release
- 1 Product/Domain lead (oil & gas document control experience)
- 1 Backend engineer
- 1 Frontend engineer
- 1 QA/automation engineer
- 1 Part-time DevOps engineer

---

## 9) Risks and mitigations
- **Risk:** slow performance with large files.
  - **Mitigation:** object storage, CDN, async processing.
- **Risk:** user adoption (too technical).
  - **Mitigation:** simple workflow UI, hide complexity.
- **Risk:** compliance gaps.
  - **Mitigation:** immutable audit logs + strict approvals.

---

## 10) First steps you can do this week
1. Decide your MVP scope (one project, one discipline).
2. Define document metadata fields and status lifecycle.
3. Build the `commit/push/pull/history` endpoints first.
4. Add workflow approvals second.
5. Pilot with real project documents early.

If you want, the next step can be a concrete **database schema + endpoint contracts** for v1.

# GitPlant EDMS MVP

GitPlant is a document-control MVP for engineering teams. It includes a FastAPI backend and a React/Vite frontend for demo authentication, document lifecycle management, approvals, transmittals, audit exports, and reporting.

## Current project state

### Backend (FastAPI + SQLModel)
- Demo bearer-token authentication (`/auth/login`, `/auth/me`) with role checks.
- Document lifecycle APIs:
  - create/search documents
  - upload PDFs and attach them to document records
  - create branches
  - commit/push/pull revisions
  - revision metadata compare + text diff
- Approval workflow:
  - submit for approval
  - approver/controller decision (approved/rejected)
- Transmittals and audit trail:
  - create/list transmittals
  - list audit events
  - export audit events as CSV and JSONL
- Reporting:
  - dashboard summary
  - dashboard extended breakdown
- Ops endpoints:
  - health/liveness/readiness checks
  - runtime storage diagnostics (`/health/info`)
  - backup/restore snapshot endpoints

### Frontend (React + Vite)
- Sign-in UI for demo account.
- Dashboard summary cards.
- Upload PDFs to create documents.
- Search and manage existing documents.

## Repository layout

- `backend/` – FastAPI app, SQLModel models, routers, tests.
- `frontend/` – React + TypeScript Vite client.
- `docker-compose.yml` – optional local PostgreSQL service.
- `docs/` – supplemental project notes.

## Quick start

### 1) Run backend
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

Backend docs: http://127.0.0.1:8000/docs

### 2) Run frontend
```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

Frontend app: http://127.0.0.1:5173

## Where data is stored

By default, data is persisted in stable, repo-anchored paths (so records do not "disappear" based on where `uvicorn` is launched):

- SQLite database: `backend/.data/edms.db`
- Uploaded PDFs: `backend/storage/documents/`

You can override these defaults with environment variables:

- `DATABASE_URL` (e.g. PostgreSQL URL or custom SQLite URL)
- `DOCUMENT_STORAGE_DIR`

Use the diagnostics endpoint to verify runtime paths:

```bash
curl http://127.0.0.1:8000/health/info
```

## Demo account
- `user@edms.local / user123`

## Validation

### Backend tests
```bash
cd backend
pytest -q
```


## Demo data tools (development only)

When `ENABLE_DEMO_TOOLS=true`, the frontend enables:

- **Seed demo data**: inserts sample documents, revisions, an approval, and audit events.
- **Reset demo**: clears document tables and stored PDF files, then reseeds demo data.

> ⚠️ These controls are intended for local/dev workflows only and should stay disabled in production.


## Project workflow (pull/merge)

GitPlant now supports a **Project Working Set** flow that maps directly to Git concepts:

- **Plant** = main branch (authoritative current revisions)
- **Project** = branch/workspace
- **Pull for project** = checkout into a project workspace
- **Merge to Plant** = promote READY working revisions to Plant

### API endpoints

- `POST /projects` create project metadata
- `GET /projects` list project summary with working document counts
- `GET /projects/{project_number}` project detail with working documents
- `POST /projects/{project_number}/pull` pull one or many docs into project working set
- `POST /projects/{project_number}/working/{working_revision_id}/ready` mark working item READY
- `POST /projects/{project_number}/working/{working_revision_id}/abandon` abandon working item
- `POST /projects/{project_number}/merge` merge READY working items into Plant
- `GET /documents` list Plant documents with `active_project_count`

### UI flow

1. Open **Documents**.
2. Select one or more docs, enter a project number (for example `PRJ-100`), and click **Pull selected for project**.
3. Open **Projects** to see Projects Summary.
4. Open the project detail, mark individual items **READY**.
5. Click **Merge to Plant** to promote READY items.

### Acceptance test checklist

1. Create project `PRJ-100` and pull `DOC-001` + `DOC-002`.
2. Projects Summary shows `PRJ-100` with count `2`.
3. Project detail shows both docs in `WORKING`.
4. Mark `DOC-001` as `READY`.
5. Merge project merges only `DOC-001`; `DOC-002` remains `WORKING`.
6. Documents list shows `DOC-001` current Plant revision updated.
7. Restart backend; data remains available.
8. Audit events exist for pull, ready, and merge actions.

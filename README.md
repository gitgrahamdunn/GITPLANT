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
- Documents (Plant) view with active-project pull workflow guardrails.
- Projects workspace with Working/Ready/Merged actions and merge confirmation.
- Dedicated Plant Upload page separate from project working uploads.

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


## EDMS workflow (Plant vs Project)

The enforced workflow is now:

1. **Create Project** (required `project_number`)
2. **Pull Documents into Project** (ACTIVE projects only)
3. **Edit outside system scope**
4. **Upload working revision in Project**
5. **Mark READY + Push to Plant**

### Roles and upload boundaries

- **Plant Upload** (`Plant Upload` navigation): updates Plant current revision directly.
- **Project working upload** (`Projects` → project detail): uploads file into project working revision only; Plant is unchanged until merge.

### Core API endpoints

- `POST /projects` create project
- `GET /projects?status=ACTIVE` list active projects for pull dropdown
- `POST /projects/{project_id}/pull` pull one or more documents to project
- `POST /projects/{project_id}/working/{working_revision_id}/upload` upload working revision file
- `POST /projects/{project_number}/working/{working_revision_id}/ready` mark ready
- `POST /projects/{project_number}/merge` merge READY docs to Plant
- `POST /documents/{document_id}/plant/upload` upload directly to Plant revision

### UI behavior guardrails

- Pull is disabled when no ACTIVE projects exist, with CTA **Create a project first**.
- Pull target is selected from ACTIVE project dropdown (no free-text project number).
- Project detail includes status badges: `WORKING`, `READY`, `MERGED`, `ABANDONED`.
- Push to Plant includes confirmation and merges only READY items.

### Acceptance walk-through

1. Create project `PRJ-200`.
2. Open **Documents (Plant)**, select `DOC-001`, and pull via ACTIVE project dropdown.
3. Open project detail and verify `DOC-001` appears under **Working**.
4. Upload working revision in project row.
5. Mark item **READY** and click **Push to Plant**.
6. Verify Plant document revision increments.
7. Restart backend and verify records persist (SQLite path under `backend/.data/edms.db`).

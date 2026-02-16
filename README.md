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

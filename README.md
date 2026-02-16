# GitPlant EDMS MVP

GitPlant is a document-control MVP for engineering teams. It includes a FastAPI backend and a React/Vite frontend for demo authentication, document lifecycle management, approvals, transmittals, audit exports, and basic reporting.

## Current project state

### Backend (FastAPI + SQLModel)
- Demo bearer-token authentication (`/auth/login`, `/auth/me`) with role checks.
- Document lifecycle APIs:
  - create/search documents
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
  - liveness/readiness health checks
  - backup/restore snapshot endpoints

### Frontend (React + Vite)
- Sign-in UI for demo accounts.
- Session profile view with sign-out.
- Role-aware dashboard behavior:
  - approver/document-controller users see dashboard summary cards
  - engineer users can still sign in and use search without dashboard errors
- Document search table wired to backend search response shape.

## Repository layout

- `backend/` – FastAPI app, SQLModel models, routers, tests.
- `frontend/` – React + TypeScript Vite client.
- `docker-compose.yml` – local PostgreSQL service.
- `docs/` – supplemental project notes.

## Quick start

### 1) Start PostgreSQL
```bash
docker compose up -d postgres
```

### 2) Run backend
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

Backend docs: http://127.0.0.1:8000/docs

### 3) Run frontend
```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

Frontend app: http://127.0.0.1:5173

## Demo accounts
- `controller@edms.local / controller123`
- `engineer@edms.local / engineer123`
- `approver@edms.local / approver123`

## Validation

### Backend tests
```bash
cd backend
pytest -q
```

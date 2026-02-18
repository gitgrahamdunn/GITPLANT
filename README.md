# GitPlant EDMS MVP

GitPlant is a document-control MVP for engineering teams.

## Workflow mapping

- **Plant** = `main` branch (source of truth documents)
- **Project** = pull request against Plant
- Project detail behaves like a PR page with Conversation / Files changed / Checks and merge action.

## Quick start

### 1) Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
ENABLE_DEMO_TOOLS=true uvicorn app.main:app --reload
```

Backend: http://127.0.0.1:8000/docs

### 2) Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend: http://127.0.0.1:5173

## Demo account

- `user@edms.local / user123`

## Dev demo-data controls

When `ENABLE_DEMO_TOOLS=true`, the app exposes:

- `POST /dev/seed` -> wipe and reseed synthetic SQLite demo data (documents + projects + working revisions + audit events)
- `POST /dev/reset` -> wipe all demo data
- `GET /dev/status` -> counts of seeded entities
- `POST /dev/audit/ui` -> dev-only UI interaction audit sink

You can also seed from script:

```bash
cd backend
python scripts/seed_demo.py
```

## Persistence

- SQLite DB path defaults to `backend/.data/edms.db`
- Document storage defaults to `backend/storage/documents`
- Runtime path diagnostics: `GET /health/info`

## Validation commands

```bash
cd backend && pytest -q
cd frontend && npm run build
```

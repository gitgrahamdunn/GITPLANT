# GitPlant EDMS MVP

GitPlant is a document-control MVP for engineering teams.

## Workflow mapping

- **Code (Plant)** = `main` branch (source of truth documents)
- **Pull Request (Project)** = project workflow against Plant

## Quickstart

From repository root, run one command:

```bash
npm run dev
```

This starts both:
- Backend API on `http://127.0.0.1:8000`
- Frontend UI on `http://127.0.0.1:5173`

## Single-server mode (API + UI on one port)

```bash
npm run start
```

This builds frontend and serves it via FastAPI at `http://127.0.0.1:8000`.

## Demo account

- `user@edms.local / user123`

## Demo controls

Dev endpoints are enabled automatically when `APP_ENV=dev` (or explicitly with `ENABLE_DEMO_ENDPOINTS=true`).

- `POST /dev/seed` → wipe + reseed docs/projects/audit events + placeholder PDFs
- `POST /dev/reset` → wipe demo data + storage
- `GET /dev/status` → enabled flag + reason + entity counts

## Testing (single command)

```bash
npm test
```

This runs:
- backend pytest suite
- scripted frontend/backend happy-path flow

## Persistence

- SQLite DB path defaults to `backend/.data/edms.db`
- Plant storage defaults to `backend/storage/plant`
- Document upload storage defaults to `backend/storage/documents`


## Vercel deployment notes

- Set `VITE_API_URL` in the frontend environment to your deployed backend URL (for example `https://<your-backend>.vercel.app`).
- Backend CORS allows:
  - `https://gitplant-oggy.vercel.app`
  - any `https://*.vercel.app` origin (for Vercel preview deployments)
- CORS preflight `OPTIONS` requests are handled by FastAPI `CORSMiddleware`.

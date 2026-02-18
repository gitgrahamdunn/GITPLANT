# GitPlant Frontend

React + Vite frontend for the EDMS backend.

## Features
- Demo login (`/auth/login`)
- Profile check (`/auth/me`)
- Projects summary + project detail workflow (`/projects`)
- Pull selected documents into project working sets
- Mark READY / Abandon / Merge to Plant from project detail
- Document search (`/documents` and `/documents/search`)

## Environment configuration

Set `VITE_API_URL` to your backend origin (no trailing slash). The frontend now reads this value for all API requests.

```bash
cd frontend
cp .env.example .env
# local backend example
VITE_API_URL=http://127.0.0.1:8000
```

If `VITE_API_URL` is missing, the app logs a clear `console.error` and falls back to same-origin requests.

### Vercel setup

In the Vercel frontend project, add:

- `VITE_API_URL=https://gitplant-backend.vercel.app`

Then redeploy so auth/login requests target the deployed backend.

## Run locally
```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

Open http://127.0.0.1:5173

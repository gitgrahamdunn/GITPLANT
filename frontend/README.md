# GitPlant Frontend

React + Vite frontend for the EDMS backend.

## Features
- Demo login (`/auth/login`)
- Profile check (`/auth/me`)
- Projects summary + project detail workflow (`/projects`)
- Pull selected documents into project working sets
- Mark READY / Abandon / Merge to Plant from project detail
- Document search (`/documents` and `/documents/search`)

## Run locally
```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

Open http://127.0.0.1:5173

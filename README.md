# Gitplant Pass 1 (Desktop-first)

This repository now contains the Pass 1 desktop-first vertical slice defined in `docs/PDF_REVIEW_ARCHITECTURE_PACKAGE.md`.

## Workspace structure

- `apps/desktop` – Tauri desktop shell + React/TypeScript UI
- `apps/desktop/src-tauri` – Rust native commands, SQLite schema, managed file storage
- `packages/shared-types` – shared contracts
- `packages/viewer-core` – renderer abstraction interfaces
- `packages/viewer-pdfjs` – PDF.js renderer adapter implementation
- `packages/persistence-core` – persistence gateway interfaces used by UI

## Prerequisites

- Node.js 20+
- Rust stable toolchain
- Tauri system dependencies: https://v2.tauri.app/start/prerequisites/

## Commands

From repository root:

- Dev (one command): `npm run desktop:dev`
- Desktop build: `npm run desktop:build`
- Tests: `npm test`
- Typecheck: `npm run typecheck`

## Pass 1 manual verification checklist

1. Run `npm run desktop:dev` and confirm desktop window opens.
2. Click **Import PDF**, pick a local `.pdf` through native picker.
3. Confirm document appears in viewer and page renders.
4. Use **Prev/Next** and **Zoom In/Zoom Out/Fit Width**.
5. Confirm imported document appears in **Recent Documents**.
6. Restart app and confirm recent item reopens.

## Deferred to Pass 2+

- Markup tools/redlines/comments/workflow
- Collaboration/sync/export pipeline
- Native renderer adapter
- Advanced performance optimization and tile rendering

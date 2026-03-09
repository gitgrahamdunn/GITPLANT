# Gitplant Pass 1.5 (Desktop-first architecture upgrade)

This repository now includes the architectural upgrade for multi-layer viewing, document transformations, and processing/indexing scaffolding.

Design authority: `docs/PDF_REVIEW_ARCHITECTURE_PACKAGE.md`.

## Repo/package structure

- `apps/desktop` – Tauri shell + React UI
- `apps/desktop/src-tauri` – Rust commands, SQLite schema, managed storage, transform + processing proof paths
- `packages/shared-types` – domain/shared records for revisions, jobs, extracted text
- `packages/viewer-core` – renderer abstraction + render-scene/layer model
- `packages/viewer-pdfjs` – PDF.js adapter implementation
- `packages/persistence-core` – UI persistence gateway contracts
- `packages/document-transform-core` – transform command/result contracts
- `packages/document-transform-pdflib` – adapter slot (desktop implementation currently in Rust service)
- `packages/processing-core` – processing job and OCR provider contracts
- `packages/text-extraction-core` – text extraction provider contracts

## What changed

- Viewer architecture now models stacked render layers (`base_pdf`, `overlay_pdf`, future markup/selection overlays).
- Transformations are isolated behind dedicated command boundary and create **derived revisions**.
- Processing pipeline tracks jobs and stores extracted page text by revision/page.
- Schema supports immutable originals, revision lineage, processing jobs, extracted text, and audit events.
- Desktop app includes minimal dev scaffolding buttons to trigger text extraction and extract-page transformation proof path.

## Implemented now (real paths)

1. Import + open PDFs (existing behavior still supported).
2. Extract page range to a new derived revision (managed storage + metadata persistence).
3. Trigger text extraction job for current revision and persist per-page text.

## Scaffolded for later

- OCR provider implementation (boundary and job type already in place)
- Full transform UI for delete/insert/reorder/combine
- Native renderer adapter implementation
- Full markup/selection overlay rendering

## Commands

From repository root:

- Dev (desktop): `npm run desktop:dev`
- Desktop build: `npm run desktop:build`
- Tests: `npm test`
- Typecheck: `npm run typecheck`

## Manual verification checklist

1. Run `npm run desktop:dev` and confirm desktop window opens.
2. Import a PDF and confirm page rendering still works.
3. Click **Extract page 1 to derived revision** and confirm no crash + viewer shows comparison-capable scene layer info.
4. Click **Trigger text extraction** and confirm extracted row count updates.
5. Restart app and confirm recent document still opens.

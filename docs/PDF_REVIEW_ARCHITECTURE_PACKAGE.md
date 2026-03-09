# Desktop-First Engineering PDF Review — Architecture Package

## Executive summary
The desktop app remains local-first (Tauri + React + SQLite + managed filesystem), but architecture is now explicitly upgraded for:
- multi-layer page rendering/comparison,
- immutable document transformations with derived revisions,
- OCR/indexing processing pipelines with per-page text persistence.

## Updated architecture blueprint

### Subsystems and boundaries
- **Renderer abstraction (`packages/viewer-core`)**
  - Owns `RenderScene`, `RenderLayer`, viewport contracts, renderer interface.
- **PDF.js adapter (`packages/viewer-pdfjs`)**
  - Implements renderer contract and text-content hooks for searchable PDFs.
- **Future native renderer adapter slot**
  - Kept behind the same viewer-core interface; UI stays adapter-agnostic.
- **Document transformation engine (`packages/document-transform-core` + Tauri Rust service)**
  - Owns transformation commands/results and derived-revision lifecycle.
- **OCR/indexing processing pipeline (`packages/processing-core` + `packages/text-extraction-core` + Tauri Rust service)**
  - Owns processing jobs, status transitions, and extracted text storage.
- **Persistence core + SQLite (`packages/persistence-core`, `apps/desktop/src-tauri`)**
  - Owns revision lineage, jobs, extracted text, and audit events.
- **Desktop UI (`apps/desktop/src`)**
  - Uses abstractions only (viewer-core/persistence contracts), not PDF.js internals.

## Domain model update

### Document
Stable identity for a managed engineering document.

### DocumentRevision
- immutable file snapshot
- `source_revision_id` nullable for lineage
- `derivation_type` nullable for transformation provenance

### PageAsset / PageRenderCache metadata (scaffold)
- optional cache metadata keyed by revision/page/render params

### DocumentTransformationJob
- command intent + execution status + output revision

### ProcessingJob
- `job_type`: `text_extraction | ocr | thumbnail_generation | export`
- `status`: `pending | running | completed | failed`

### ExtractedPageText
- page-addressable extracted/search text stored independently from raster output

### ComparisonSession
- viewer state linking base revision + optional overlay revision + current page/viewport

### AuditEvent
- immutable records for transformation and processing events

## Multi-layer viewer model
Viewer scene is layer-based, not single-raster based:
- `LayerKind`: `base_pdf`, `overlay_pdf`, `markup_overlay`, `selection_overlay`
- per-layer visibility, opacity, transform placeholders
- supports base-only scene today and optional second PDF layer for comparison proof

## Persistence model (SQLite)
Key entities:
- `documents`
- `document_revisions` (lineage + derivation)
- `processing_jobs`
- `extracted_page_text`
- `audit_events`
- `recent_documents`

## Implemented now vs scaffolded

### Implemented now
- base + optional overlay layer scene modeling in viewer-core/UI
- one real transformation proof path: extract page range into derived revision
- real text extraction job path for searchable PDFs with per-page text persistence
- audit events for transformation + processing completions

### Scaffolded for later
- full OCR provider implementation
- full UI for all transform operations
- markup/selection overlay rendering engines (layer slots are ready)
- native renderer adapter implementation

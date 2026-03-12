# Desktop-First Product Architecture Blueprint

This document aligns with:

- `docs/PDF_REVIEW_ARCHITECTURE_PACKAGE.md`
- `docs/PROJECT_HANDOFF_SUMMARY.md`

## Product scope

Gitplant is a **desktop-first engineering PDF review and squad check tool**.

## Core extension points locked in

- renderer abstraction layer (`packages/viewer-core`)
- PDF.js adapter (`packages/viewer-pdfjs`)
- future native renderer adapter slot
- document transformation engine boundary
- processing pipeline boundary
- multi-layer render scene model
- local persistence for revisions, markups, jobs, extracted text, reminders, and audit events

## Product capabilities targeted by this architecture

- fast PDF viewing
- structured markups
- threaded comments
- squad check workflows
- review confirmations
- reminder automation
- audit trail
- revision comparison through overlay rendering

## Domain essentials

- `Workspace`
- `Project`
- `Document`
- `DocumentRevision`
- `MarkupLayer`
- `MarkupObject`
- `CommentThread`
- `ReviewerAssignment`
- `SquadCheck`
- `Confirmation`
- `Reminder`
- `ProcessingJob`
- `ExtractedPageText`
- `AuditEvent`

## Architectural guardrails

1. UI/viewer code must not directly import PDF.js internals.
2. Transform operations must create new revisions; no in-place mutation of originals.
3. OCR and text extraction are processing concerns, not rendering concerns.
4. Rust/Tauri owns persistence and processing.
5. The desktop runtime is the primary runtime for core product behavior.
6. Markups and comments must be modeled as first-class product entities, not ad hoc viewer annotations.

## Runtime split

### Rust/Tauri service layer

Owns:

- SQLite schema and migrations
- managed file storage
- document import
- revision lineage
- transformation execution
- processing job execution
- text extraction
- export pipeline
- native desktop features

### TypeScript/React UI layer

Owns:

- app shell and workflows
- viewer state
- tool state
- markup editing UX
- threaded comment UX
- review workflow UX
- renderer abstraction consumption
- shared contracts and view models

## Viewer model

The render scene is layer-based.

Layer kinds:

- `base_pdf`
- `overlay_pdf`
- `markup_overlay`
- `selection_overlay`

Layer system requirements:

- visibility toggles
- opacity control
- stacking order
- multi-document overlay support
- independent overlay redraw paths

## Document and revision model

PDF files are immutable originals.
User-facing edit operations create derived revisions.

Required revision lineage fields:

- `source_revision_id`
- `derivation_type`

Supported/future derivations:

- extract pages
- delete pages
- insert pages
- reorder pages
- combine PDFs

## Processing model

Separate processing job system with job types such as:

- `text_extraction`
- `ocr`
- `thumbnail_generation`
- `export`

Extracted text is stored per page and per revision.

## Persistence model

Important persisted entities include:

- `documents`
- `document_revisions`
- `markup_layers`
- `markup_objects`
- `comment_threads`
- `reviewer_assignments`
- `squad_checks`
- `confirmations`
- `reminders`
- `processing_jobs`
- `extracted_page_text`
- `audit_events`
- `recent_documents`

## Immediate next implementation pass

### Pass 2 — markup overlay engine

Priority work:

- markup object model
- drawing tools
- comment attachment
- selection model
- persistence of markups
- overlay rendering integration
- undo/redo foundations
- hit testing

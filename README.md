# Gitplant

Gitplant is a **desktop-first collaborative engineering PDF review tool** for squad check and drawing-review workflows.

## Product direction

Gitplant is being built for:

- fast PDF viewing
- structured markups
- threaded comments
- squad check workflows
- review confirmations
- reminder automation
- audit trails
- revision comparison with overlay mode

Reference products are closer to **Bluebeam**, **Acrobat review**, and engineering drawing review tools.

## Architecture source of truth

Primary architecture document:

- `docs/PDF_REVIEW_ARCHITECTURE_PACKAGE.md`

Supporting documents:

- `docs/DESKTOP_FIRST_ARCHITECTURE.md`
- `docs/PROJECT_HANDOFF_SUMMARY.md`

## Locked architecture decisions

### Desktop first

Gitplant runs as a **Tauri desktop app**.

Stack:

- Tauri
- React + TypeScript
- Vite
- Rust service layer
- SQLite
- PDF.js renderer adapter

The intended developer entry point is a single desktop command:

```bash
npm run desktop:dev
```

### Service ownership

**Rust/Tauri is the authoritative application service layer.**

Rust owns:

- SQLite persistence
- document import
- file storage
- derived revision creation
- processing jobs
- text extraction
- export operations
- desktop-native integrations

TypeScript owns:

- UI
- viewer state
- renderer abstraction usage
- markup model
- workflow UI
- shared contracts

### Renderer boundary

Rendering must remain replaceable.

Current renderer:

- PDF.js

Architecture slots:

- `packages/viewer-core`
- `packages/viewer-pdfjs`
- future native renderer adapter

The UI must not import PDF.js internals directly.

### Viewer model

The viewer is layer-based.

Current/future layer kinds:

- `base_pdf`
- `overlay_pdf`
- `markup_overlay`
- `selection_overlay`

This supports revision comparison, markups, anchored comments, and future selection tools.

## Core domain model

Primary entities include:

- Workspace / Project
- Document
- DocumentRevision
- MarkupLayer
- MarkupObject
- CommentThread
- ReviewerAssignment
- SquadCheck
- Confirmation
- Reminder
- AuditEvent
- ProcessingJob
- ExtractedPageText

PDF files are treated as immutable originals. Transformations create **derived revisions**.

## Current implementation status

Implemented now:

- desktop shell
- PDF import
- managed local file storage
- SQLite persistence
- document revision model
- renderer abstraction
- PDF.js adapter
- basic viewer
- page navigation
- zoom
- recent documents list
- text extraction pipeline
- extract-pages transformation proof path

Scaffolded / next:

- markup engine
- threaded comments
- squad check workflow
- review confirmations
- reminder automation
- export pipeline
- collaboration/sync

## Commands

From the repository root:

```bash
npm run desktop:dev
npm run desktop:build
npm test
npm run typecheck
```

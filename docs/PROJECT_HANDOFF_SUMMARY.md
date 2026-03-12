# Project Handoff Summary

## Gitplant: Desktop PDF Review / Squad Check Tool

Gitplant is a **desktop-first collaborative engineering PDF review tool** for squad check and drawing review workflows.

## Product goals

Primary capabilities:

1. fast PDF viewing
2. structured markup system
3. threaded comments
4. squad check workflow
5. review confirmations
6. reminder automation
7. audit trail
8. revision comparison with overlay mode

Target users include engineering teams reviewing large drawings, redlines, and coordinated design changes.

## Product shape

Gitplant should feel closer to:

- Bluebeam
- Acrobat review
- collaborative drawing review tools

with stronger workflow automation and collaboration.

## Locked architecture decisions

### Desktop first

The application runs as a Tauri desktop app.

Stack:

- Tauri desktop shell
- React + TypeScript UI
- Vite build system
- Rust service layer
- SQLite local database
- PDF.js renderer adapter

The intended runtime is a single desktop application, not a multi-service web stack.

### Service ownership

Rust/Tauri is the authoritative application service layer.

Rust handles:

- SQLite database
- document import
- file storage
- derived revision creation
- processing jobs
- text extraction
- export operations
- desktop native functionality

TypeScript handles:

- UI
- viewer state
- renderer abstraction
- markup model
- workflow UI
- shared domain contracts

### Rendering architecture

Rendering must remain replaceable.

Current renderer:

- PDF.js

Required architecture boundary:

- `viewer-core`
- `viewer-pdfjs`
- future native renderer slot

The UI must never import PDF.js directly.

### Viewer architecture

The viewer supports multi-layer rendering.

Layer kinds:

- `base_pdf`
- `overlay_pdf`
- `markup_overlay`
- `selection_overlay`

This enables:

- revision comparison
- future markups
- selection highlights
- comment anchors

## Document model

PDF files are treated as immutable originals.
Operations create derived revisions.

Core entities:

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

## Transformation engine

Page operations belong in a document transformation service.

Supported future operations:

- delete pages
- insert pages
- reorder pages
- extract pages
- combine PDFs

All operations produce new revisions.
Original PDFs remain untouched.

## Processing pipeline

Separate processing job system.

Supported job types:

- `text_extraction`
- `ocr`
- `thumbnail_generation`
- `export`

Current implementation:

- text extraction for PDFs that already contain text
- OCR scaffolded but not yet implemented

## Data storage

Local-first architecture:

- SQLite database
- local PDF file storage
- structured markup storage
- processing jobs
- audit events

Important tables/entities:

- `documents`
- `document_revisions`
- `recent_documents`
- `processing_jobs`
- `extracted_page_text`
- `audit_events`

## Current implementation status

Completed:

- desktop shell
- PDF import
- local file storage
- SQLite persistence
- document revision model
- renderer abstraction
- PDF.js adapter
- basic viewer
- page navigation
- zoom
- recent documents list
- text extraction pipeline
- extract pages transformation
- architecture documentation

## Development workflow

### Pass 2 — next

Markup engine:

- overlay drawing layer
- markup persistence
- comment threads
- selection system
- undo/redo
- hit testing

### Pass 3

Workflow system:

- reviewer assignments
- squad check confirmations
- reminders
- status filters

### Pass 4

Export pipeline:

- flattened PDF exports
- markup embedding
- audit report generation

### Pass 5

Collaboration:

- live syncing
- multi-user presence
- comment updates

## Immediate next task

**Pass 2: markup overlay engine**

Add:

- markup object model
- markup drawing tools
- comment attachment
- selection model
- persistence of markups
- overlay rendering integration

This is the core product IP direction.

## One-line summary

Gitplant is a desktop-first collaborative engineering PDF review tool focused on fast PDF viewing, structured markups, comment collaboration, squad check workflows, audit tracking, and revision comparison with a replaceable renderer and local-first architecture.

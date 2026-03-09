# Desktop-First Product Architecture Blueprint

## 1) Desktop-First Architecture Blueprint

### Product direction
A local-first desktop application for engineering PDF review that treats **structured markup overlays** as the system of record and uses PDFs as immutable source artifacts.

### Core architectural principles
1. **Desktop-native runtime**: Tauri shell is the only application runtime in normal use (no dependency on separate frontend/backend servers).
2. **Local-first data ownership**: SQLite + local filesystem are primary persistence layers.
3. **Offline-capable by default**: review, markup, comments, workflow state changes, and exports must work without network.
4. **Deterministic rendering + reversible edits**: PDF content is read-only; user intent lives in typed markup/comment/workflow entities.
5. **Traceability**: every meaningful state change emits an audit event.
6. **Modular boundaries from day one**: document pipeline, markup engine, workflow engine, persistence, and export service are isolated modules.

### Runtime topology
- **Tauri Core (Rust)**
  - App lifecycle and windowing
  - Secure command surface (`invoke`) to frontend
  - SQLite access (via `sqlx`/`rusqlite`) behind repository layer
  - File I/O for PDF import/storage/export
  - Export pipeline orchestration (PDF + overlays flattening)
  - Audit event write-through
- **Frontend (React + TypeScript)**
  - UI shells: Project, Document, Review Workspace, Workflow Inbox
  - PDF.js viewer integration
  - Overlay rendering layer for markups and comment anchors
  - Local state (UI/session) + command/query client for Tauri APIs
  - Validation and optimistic UI updates with rollback on persistence failure
- **Local storage**
  - SQLite database: metadata, overlays, workflow objects, audit trail
  - Filesystem store: imported source PDFs, generated export artifacts, thumbnails/cache

### Logical module decomposition
- `workspace`: project/document navigation and context loading
- `pdf_viewer`: PDF.js wrappers (page loading, viewport transforms, text layer hooks)
- `markup_engine`: shape models, hit-testing, coordinate transforms, editing tools
- `comments_engine`: threaded comments anchored to markup/page coordinates
- `workflow_engine`: reviewer assignment, squad checks, confirmations, reminders
- `persistence`: repositories and migrations for SQLite + file index
- `export_engine`: builds marked-up PDF outputs and review packages
- `audit_engine`: standardized event creation for all state transitions

### Security and reliability baseline
- Tauri allowlist/capabilities locked to needed FS paths and commands only
- All writes in explicit transactions where entities are coupled
- Schema versioning + migrations at startup
- Crash-safe saves: append audit first, commit entity transaction, then fs sync where applicable
- Input validation for imported files and JSON payloads

---

## 2) Recommended Repo Structure (Tauri + React + SQLite + PDF.js)

```text
GITPLANT/
  apps/
    desktop/
      src-tauri/
        Cargo.toml
        tauri.conf.json
        src/
          main.rs
          app/
            mod.rs
            commands/
              projects.rs
              documents.rs
              markups.rs
              comments.rs
              workflow.rs
              export.rs
            services/
              pdf_store.rs
              export_service.rs
              audit_service.rs
            db/
              mod.rs
              connection.rs
              migrations.rs
              repositories/
                projects_repo.rs
                documents_repo.rs
                markups_repo.rs
                comments_repo.rs
                workflow_repo.rs
                audit_repo.rs
            models/
              project.rs
              document.rs
              revision.rs
              markup.rs
              comment_thread.rs
              reviewer_assignment.rs
              squad_check.rs
              confirmation.rs
              reminder.rs
              audit_event.rs
      src/
        main.tsx
        app/
          AppShell.tsx
          routes.tsx
        modules/
          workspace/
          viewer/
            PdfViewer.tsx
            pdfjs.ts
            viewport.ts
          markup/
            OverlayCanvas.tsx
            tools/
            serialization.ts
          comments/
          workflow/
          export/
        state/
          queryClient.ts
          stores/
        types/
          domain.ts
          dto.ts
        styles/
  packages/
    shared-types/
      src/
        domain.ts
        events.ts
  migrations/
    sqlite/
      0001_init.sql
      0002_markup_workflow.sql
  docs/
    DESKTOP_FIRST_ARCHITECTURE.md
    MIGRATION_GUIDE_WEB_TO_DESKTOP.md
```

### Notes
- Frontend and Tauri Rust code are co-located under one desktop app package.
- No operational dependency on separate web backend process.
- Existing browser-first backend/frontend can be retained temporarily behind `legacy/` during migration.

---

## 3) Domain Model

### Project
- `id` (UUID)
- `name` (string)
- `description` (string?)
- `status` (`active|archived`)
- `created_at`, `updated_at`

### Document
- `id` (UUID)
- `project_id` (FK)
- `title` (string)
- `discipline` (string?)
- `current_revision_id` (FK?)
- `created_at`, `updated_at`

### DocumentRevision
- `id` (UUID)
- `document_id` (FK)
- `revision_label` (string, e.g., A, B, IFC-01)
- `source_pdf_path` (filesystem path)
- `page_count` (int)
- `checksum_sha256` (string)
- `imported_at`
- `is_superseded` (bool)

### Markup
- `id` (UUID)
- `document_revision_id` (FK)
- `page_number` (int)
- `type` (`cloud|line|arrow|text|stamp|highlight|dimension|symbol`)
- `geometry` (JSON: normalized coordinates)
- `style` (JSON: color, thickness, opacity)
- `content` (JSON: optional text/payload)
- `status` (`open|resolved|void`)
- `created_by`, `created_at`, `updated_at`

### CommentThread
- `id` (UUID)
- `document_revision_id` (FK)
- `markup_id` (FK nullable for page-level thread)
- `page_number` (int)
- `anchor` (JSON point/rect normalized)
- `state` (`open|resolved`)
- `created_by`, `created_at`, `updated_at`
- child `CommentMessage`: `id`, `thread_id`, `author`, `body`, `created_at`, `edited_at?`

### ReviewerAssignment
- `id` (UUID)
- `project_id` (FK)
- `document_revision_id` (FK)
- `reviewer_id` (local user identity)
- `role` (`checker|approver|observer`)
- `due_at` (datetime?)
- `status` (`pending|in_progress|completed|reassigned`)
- `created_at`, `updated_at`

### SquadCheck
- `id` (UUID)
- `document_revision_id` (FK)
- `check_type` (`discipline|constructability|safety|qa_custom`)
- `status` (`not_started|in_progress|passed|failed`)
- `owner_assignment_id` (FK)
- `started_at`, `completed_at`
- `result_summary` (text?)

### Confirmation
- `id` (UUID)
- `target_type` (`markup|thread|squad_check|revision`)
- `target_id` (UUID)
- `confirmed_by`
- `confirmation_type` (`accepted|rejected|verified`)
- `note` (text?)
- `created_at`

### Reminder
- `id` (UUID)
- `assignment_id` (FK nullable)
- `target_type` (`thread|squad_check|revision`)
- `target_id` (UUID)
- `scheduled_for` (datetime)
- `status` (`scheduled|sent|dismissed`)
- `channel` (`in_app|email_future`)
- `created_at`, `sent_at?`

### AuditEvent
- `id` (UUID)
- `entity_type` (string)
- `entity_id` (UUID)
- `event_type` (string)
- `actor_id` (string)
- `timestamp` (datetime)
- `payload` (JSON diff/context)
- `revision` (monotonic integer or ULID for ordering)

---

## 4) Data Flows

### A) Opening a PDF
1. User selects file in desktop UI.
2. Frontend calls Tauri command `import_document_revision` with file path + project/document context.
3. Rust service validates extension/checksum, copies file into app-managed storage.
4. Rust stores `DocumentRevision` metadata in SQLite and emits `AuditEvent(document_revision.imported)`.
5. Frontend receives revision DTO and sets active review context.

### B) Rendering a PDF page
1. Frontend PDF module opens local file via Tauri safe file API handle/path token.
2. PDF.js loads document and page bitmap/text layers.
3. Markup engine queries markups by `(document_revision_id, page_number)` from local DB.
4. Overlay canvas renders structured markups transformed to current viewport.
5. Comment anchors and workflow badges render as separate overlay layers.

### C) Creating a markup
1. User chooses tool and draws shape on overlay canvas.
2. Frontend converts screen coordinates to normalized PDF coordinates.
3. Frontend builds `CreateMarkupInput` and invokes Tauri command.
4. Rust validates payload, inserts `Markup`, appends `AuditEvent(markup.created)` in transaction.
5. Frontend updates local state with persisted markup ID and timestamp.

### D) Attaching comments
1. User opens/creates thread from markup or page anchor.
2. Frontend invokes `create_or_append_comment_thread`.
3. Rust upserts thread/message, updates thread state and audit trail transactionally.
4. Frontend refreshes thread panel and highlights related markup/thread anchor.

### E) Saving to SQLite
1. Every mutating command is routed through Rust repositories.
2. Repositories enforce FK integrity, status transitions, and timestamp updates.
3. Command service wraps multi-entity writes in DB transaction.
4. On success, command returns full updated aggregate DTO.
5. On failure, no partial state; frontend rolls back optimistic state.

### F) Exporting a marked-up PDF
1. User chooses export target and options (flatten overlays, include open comments, audit summary).
2. Frontend invokes `export_revision_package`.
3. Rust export service loads source PDF + markups/comments from SQLite.
4. Service applies overlay draw instructions per page and writes new PDF artifact.
5. Optional sidecar JSON/CSV includes workflow state and audit extracts.
6. Export metadata stored in DB and audit event emitted.

---

## 5) Phased Implementation Plan

### Phase 1 — Local Desktop MVP
- Bootstrap Tauri + React + TypeScript workspace.
- Integrate PDF.js viewer with page navigation and zoom.
- Implement local import/storage of PDFs and revision indexing.
- Implement core markup CRUD (cloud/arrow/text/highlight) and comment threads.
- Implement SQLite schema + migrations + audit event logging.
- Implement export of flattened marked-up PDF.

**Exit criteria**: single-user local workflow from import → markup/comment → export with durable local persistence.

### Phase 2 — Workflow Features
- Reviewer assignments and per-revision inbox.
- Squad check templates/status tracking.
- Confirmations and reminders with in-app notification center.
- Rich filtering/search over markups, threads, due items.
- Improved audit trail views and timeline.

**Exit criteria**: end-to-end desktop workflow management for engineering review cycles.

### Phase 3 — Sync/Collaboration
- Optional sync adapter (cloud or on-prem) with conflict-aware merge on overlay objects.
- Identity, roles, and encrypted sync transport.
- Shared review state, assignment updates, and audit replication.
- Background sync and offline reconciliation UX.

**Exit criteria**: multi-user collaboration while preserving local-first resilience.

---

## 6) Proposed Refactor Plan for Current Repo

### Current state (high-level)
Repository is organized as browser-first split frontend/backend with FastAPI + Vite and dev server orchestration.

### Refactor strategy
1. **Create new desktop app root**: add `apps/desktop` (Tauri + React), keep current stack as `legacy/` during migration.
2. **Extract domain contracts**: define shared TS/Rust DTO contracts for Project/DocumentRevision/Markup/etc.
3. **Re-home persistence**: move data models from HTTP backend semantics to SQLite repositories in Tauri Rust.
4. **Port UI feature slices**: migrate project/document views first, then replace browser API client with Tauri command client.
5. **Replace backend endpoints with commands**: each prior API capability becomes typed Tauri command + service layer.
6. **Introduce PDF.js workspace**: add review workspace route with overlay engine as first-class module.
7. **Add workflow modules**: assignments, squad check, confirmations, reminders, audit timeline.
8. **Sunset legacy runtime**: remove dependency on separate backend/frontend servers for production paths.

### Suggested execution sequence for this repo
- Step A: Add architecture + migration docs and agreed domain schema (this document).
- Step B: Scaffold Tauri desktop app with minimal shell and compile checks.
- Step C: Implement SQLite + migrations + project/document/revision CRUD.
- Step D: Integrate PDF.js + markup/comment flows.
- Step E: Add export engine and workflow modules.
- Step F: Decommission legacy server paths after parity checks.

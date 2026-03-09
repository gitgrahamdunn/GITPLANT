# Desktop-First Engineering PDF Review — Architecture Package

## 1. Executive summary

This product pivot should be implemented as a **desktop-first, local-first engineering PDF review system** with a strict separation between rendering infrastructure and product logic.

- **Desktop runtime**: Tauri shell + React/TypeScript UI + Vite.
- **Rendering v1**: PDF.js adapter behind a renderer interface.
- **Core product engine**: markups, comments, reviewer workflow, confirmations, reminders, audit trail.
- **Persistence**: SQLite for structured data; local filesystem for source PDFs and generated outputs.
- **Performance**: viewport/tile rendering, multi-resolution caches, prefetching, memory budgeting, and overlay independence.
- **Future-proofing**: a renderer contract that allows a native sidecar (PDFium-class) later without rewriting workflow/markup/comment logic.

This architecture is optimized for Oil & Gas engineering review of large PDFs where reliability, traceability, and desktop productivity matter more than browser-native convenience.

---

## 2. Architecture blueprint

### 2.1 Desktop application overview

**Application topology**
- **Tauri shell (Rust)**
  - Window lifecycle, secure capabilities, native menus/shortcuts
  - SQLite access and migrations
  - File-system orchestration for PDF import/export and workspace paths
  - Optional sidecar process management (future native renderer)
- **React + TypeScript frontend (Vite)**
  - Viewer workspace UI and tool system
  - Overlay rendering for markups/comments
  - Workflow boards and reviewer assignment UI
  - Event-driven state store for active document sessions
- **Local persistence**
  - SQLite as system-of-record for structured entities
  - Filesystem object store for immutable PDFs and export artifacts
  - Disk caches for tiles/thumbnails/preprocessed page assets

### 2.2 Major subsystems

1. **Workspace & Project Context**
   - Project selection, document list, revision history, current review state.
2. **Viewer Core**
   - Viewport control, page navigation, zoom/pan, hit-testing bridge.
3. **Renderer Abstraction Layer**
   - Stable interface consumed by Viewer Core.
   - Adapter implementation for PDF.js in v1.
4. **Markup Core**
   - Geometry, anchors, style models, edit operations, status transitions.
5. **Comment Core**
   - Thread lifecycle and linkage to markup/page anchors.
6. **Workflow Core**
   - Reviewer assignment, squad check, confirmations, reminders.
7. **Persistence Layer**
   - Repositories, unit-of-work transactions, migrations.
8. **Export Engine**
   - Deterministic flattening of overlays/comments/workflow summary into derived outputs.
9. **Audit Engine**
   - Immutable event capture of meaningful actions.

### 2.3 Renderer abstraction strategy

- The app never calls PDF.js APIs directly outside `viewer-pdfjs` package.
- Viewer consumes only `RendererProvider` interface and typed DTOs.
- Markup/Workflow/Persistence layers cannot import renderer implementation modules.
- Coordinate systems standardized in shared contracts (page space as normalized or document units, screen space as viewport pixels).

### 2.4 Local-first data architecture

**Data ownership rules**
- **Source of truth for review work**: SQLite rows for markups/comments/workflow/audit.
- **Source PDFs**: immutable files in workspace-managed storage.
- **Derived files**: exports/previews are reproducible outputs, never authoritative.

**Durability model**
- Writes grouped transactionally by action boundary (e.g., markup create + audit event).
- File import uses checksum and write-then-rename atomic pattern.
- Crash recovery through transaction rollback + startup integrity checks.

### 2.5 Performance strategy for large PDFs

- Virtualized page list; render only visible/near-visible pages.
- Tile-based rendering at high zoom to avoid full-page reraster costs.
- Multi-level caches (in-memory + disk-backed) keyed by document revision, page, zoom bucket, tile.
- Overlay redraw decoupled from PDF raster refresh.
- Aggressive cancellation/debouncing of stale render jobs during pan/zoom.

### 2.6 Export strategy

- Export pipeline reads:
  1) source PDF revision,
  2) filtered markup/comment/workflow state snapshot,
  3) export profile (flattening rules, included layers, stamp template).
- Output targets:
  - Flattened review PDF
  - Optional companion JSON package (structured review data)
  - Optional audit summary report
- Exports are **versioned jobs** with reproducible inputs and checksums.

### 2.7 Workflow engine boundaries

Workflow core governs:
- assignment and ownership,
- squad check progression,
- confirmations/reminders,
- status filtering and SLA-like due visibility.

Workflow core does **not**:
- perform PDF rendering,
- own geometry/hit-testing,
- write directly to files.

### 2.8 Future sync/collaboration expansion path

Design now for later optional sync:
- Local event log and change stamps on entities.
- Conflict-safe identifiers and monotonic version counters.
- Sync adapter boundary (push/pull entity deltas + file manifests) without coupling local UX to network availability.
- Collaboration remains additive; desktop-local operation remains primary mode.

### 2.9 Deployment/distribution model for desktop

- Build signed installers per OS target (MSI/EXE for Windows first, optional macOS/Linux later).
- Auto-update channel with staged rollout rings.
- Workspace storage path configurable by policy.
- Enterprise-friendly offline installer option.

### 2.10 Why this architecture is right for large engineering PDFs

- Heavy documents require native-like local I/O, memory control, and responsive view interaction.
- Engineering review value lies in markup/workflow traceability, not raw rendering APIs.
- Renderer abstraction protects long-term performance options while preserving domain logic investments.
- Local-first guarantees dependable site/offline usage common in project environments.

---

## 3. Renderer abstraction design

### 3.1 Core interface (contract)

```ts
export interface RendererProvider {
  openDocument(input: OpenDocumentInput): Promise<RendererDocumentHandle>;
  closeDocument(documentId: string): Promise<void>;
  getDocumentMetadata(documentId: string): Promise<DocumentMetadata>;
  getPageCount(documentId: string): Promise<number>;
  getPageInfo(documentId: string, pageNumber: number): Promise<PageInfo>;
  renderViewport(
    documentId: string,
    pageNumber: number,
    viewport: ViewportSpec,
    options?: RenderOptions
  ): Promise<RenderedSurface>;
  renderTile(
    documentId: string,
    pageNumber: number,
    tile: TileSpec,
    options?: RenderOptions
  ): Promise<RenderedSurface>;
  getTextContent(documentId: string, pageNumber: number): Promise<TextContentResult>;
  screenToPage(
    pageNumber: number,
    x: number,
    y: number,
    viewportState: ViewportState
  ): PagePoint;
  pageToScreen(
    pageNumber: number,
    x: number,
    y: number,
    viewportState: ViewportState
  ): ScreenPoint;
}
```

### 3.2 Adapter responsibilities

The renderer adapter **owns**:
- Loading/parsing document bytes through underlying renderer.
- Page raster and text extraction details.
- Conversion between renderer-native coordinate system and contract coordinate model.
- Render job lifecycle/cancellation and low-level caching primitives.

### 3.3 Renderer-agnostic responsibilities

The following must remain independent of PDF.js:
- Markup object schema and editing operations.
- Comment thread anchoring model.
- Workflow states and transitions.
- Persistence repositories and audit event generation.
- Export business rules (which entities included, sign-off metadata, status filters).

### 3.4 Swap strategy for native renderer later

To replace PDF.js:
1. Implement `RendererProvider` in `viewer-native` package (Tauri sidecar or Rust binding).
2. Preserve existing shared DTO contracts.
3. Keep Viewer Core integration unchanged except provider binding configuration.
4. Run renderer compatibility suite (metadata parity, coordinate transform parity, tile fidelity thresholds).

This keeps replacement scope contained to adapter package + performance tuning, not cross-application rewrite.

---

## 4. Performance strategy for large PDFs

### 4.1 Viewport-based rendering

- Use scroll virtualization; only instantiate page controllers for visible range + buffer.
- Trigger raster generation from viewport observer events.
- Cancel renders when page exits active range.

### 4.2 Tile rendering strategy

- At low/medium zoom: single full-page bitmap acceptable.
- At high zoom: split page into tiles (e.g., 512x512 or 1024x1024 logical tiles).
- Prioritize center-of-viewport tiles first; defer edge tiles.

### 4.3 Multi-resolution rendering

- Maintain zoom buckets (e.g., 0.5x, 1x, 2x, 4x equivalent DPI targets).
- Show nearest cached resolution immediately, then refine progressively.
- Prevent blocking UI on exact-resolution render completion.

### 4.4 Page/tile cache strategy

- **L1 memory cache**: recent tiles/bitmaps with weighted LRU eviction.
- **L2 disk cache**: optional persisted tile blobs keyed by checksum + render params.
- Include page rotation, crop/view mode, and color profile in cache key.

### 4.5 Lazy loading strategy

- Delay heavy metadata/text extraction until page is requested.
- Load text layer on demand (search/select mode), not unconditionally.
- Defer thumbnail generation for unopened pages.

### 4.6 Overlay redraw independence

- Markup/comment overlays rendered on independent canvas/SVG layers.
- During pan/zoom, transform overlay matrix immediately while PDF tiles refresh asynchronously.
- Editing interactions use vector model in page coordinates; no raster dependency for drag/resize feedback.

### 4.7 Memory management approach

- Global memory budget (configurable) for raster caches.
- Pressure signals trigger eviction by distance from viewport and stale zoom buckets.
- Reuse canvas buffers where possible to reduce allocations and GC churn.

### 4.8 Prefetch strategy for nearby pages

- Prefetch next/previous pages based on scroll direction and speed.
- Prefetch limited tile ring around current viewport at likely next zoom bucket.
- Stop prefetch under active editing bursts or memory pressure.

### 4.9 Bottlenecks and mitigations (engineering PDFs)

1. **Very large vector-heavy pages**
   - Mitigation: tile render + job cancellation + progressive detail.
2. **Frequent zoom/pan during redline review**
   - Mitigation: debounced rerender, matrix-transformed overlays, stale job pruning.
3. **Large markups per page**
   - Mitigation: spatial index for hit-testing and partial overlay redraw.
4. **High page-count documents (hundreds/thousands)**
   - Mitigation: strict page virtualization and metadata lazy load.

---

## 5. Domain model

### 5.1 Workspace/Project
- **Purpose**: logical container for documents, users, and review workflow scope.
- **Key fields**: `id`, `name`, `code`, `facility`, `status`, `createdAt`, `updatedAt`.
- **Relationships**: one-to-many with `Document`, `ReviewerAssignment`, `Reminder`.
- **Lifecycle**: `active -> archived`.

### 5.2 Document
- **Purpose**: stable identity for an engineering deliverable across revisions.
- **Key fields**: `id`, `workspaceId`, `documentNumber`, `title`, `discipline`, `currentRevisionId`, `status`.
- **Relationships**: one-to-many with `DocumentRevision`; one current revision pointer.
- **Lifecycle**: `drafted -> under_review -> accepted -> superseded`.

### 5.3 DocumentRevision
- **Purpose**: immutable imported PDF revision and associated review context.
- **Key fields**: `id`, `documentId`, `revisionLabel`, `filePath`, `checksumSha256`, `pageCount`, `importedAt`, `isCurrent`.
- **Relationships**: one-to-many with `MarkupLayer`, `ReviewerAssignment`, `SquadCheck`, `ExportJob`.
- **Lifecycle**: `imported -> active_review -> closed`.

### 5.4 MarkupLayer
- **Purpose**: logical grouping/filtering boundary for markup visibility and export.
- **Key fields**: `id`, `revisionId`, `name`, `kind` (discipline/reviewer/system), `visibility`, `locked`.
- **Relationships**: one-to-many with `MarkupObject`.
- **Lifecycle**: `active -> locked -> archived`.

### 5.5 MarkupObject
- **Purpose**: atomic redline/annotation element on a page.
- **Key fields**: `id`, `layerId`, `pageNumber`, `type`, `geometryJson`, `styleJson`, `status`, `createdBy`, `updatedBy`, `createdAt`, `updatedAt`.
- **Relationships**: optional one-to-one or one-to-many with `CommentThread`; linked audit events.
- **Lifecycle**: `open -> resolved -> reopened` (or `void` for invalidated markups).

### 5.6 CommentThread
- **Purpose**: conversation anchored to markup or page region.
- **Key fields**: `id`, `revisionId`, `markupObjectId?`, `pageNumber`, `anchorJson`, `state`, `createdBy`, `createdAt`, `updatedAt`.
- **Relationships**: one-to-many with `Comment`.
- **Lifecycle**: `open -> resolved -> reopened`.

### 5.7 Comment
- **Purpose**: message item within a thread.
- **Key fields**: `id`, `threadId`, `authorId`, `body`, `mentionsJson`, `createdAt`, `editedAt?`, `deletedAt?`.
- **Relationships**: belongs to `CommentThread`.
- **Lifecycle**: `active -> edited -> deleted` (soft-delete for auditability).

### 5.8 ReviewerAssignment
- **Purpose**: assigns review responsibility to a person/role for revision scope.
- **Key fields**: `id`, `workspaceId`, `revisionId`, `reviewerId`, `role`, `dueAt`, `status`, `assignedBy`, `assignedAt`.
- **Relationships**: can own `SquadCheck` and be referenced by reminders.
- **Lifecycle**: `pending -> in_progress -> completed` or `reassigned`.

### 5.9 SquadCheck
- **Purpose**: structured multidisciplinary check activity tied to revision.
- **Key fields**: `id`, `revisionId`, `checkType`, `ownerAssignmentId`, `status`, `result`, `startedAt`, `completedAt`.
- **Relationships**: may require `Confirmation` records before pass state.
- **Lifecycle**: `not_started -> in_progress -> confirmed_pass|confirmed_fail`.

### 5.10 Confirmation
- **Purpose**: explicit acknowledgment/acceptance against workflow targets.
- **Key fields**: `id`, `targetType`, `targetId`, `confirmedBy`, `decision`, `note`, `createdAt`.
- **Relationships**: references `MarkupObject`, `CommentThread`, or `SquadCheck` targets.
- **Lifecycle**: append-only decision records (no hard overwrite).

### 5.11 Reminder
- **Purpose**: time-based nudges for pending assignments/checks/resolutions.
- **Key fields**: `id`, `workspaceId`, `targetType`, `targetId`, `recipientId`, `dueAt`, `sentAt?`, `status`.
- **Relationships**: linked to assignments/checks/threads.
- **Lifecycle**: `scheduled -> sent -> acknowledged|expired`.

### 5.12 AuditEvent
- **Purpose**: immutable compliance trace of state-changing actions.
- **Key fields**: `id`, `workspaceId`, `entityType`, `entityId`, `action`, `actorId`, `timestamp`, `payloadJson`, `hash`.
- **Relationships**: references any domain entity.
- **Lifecycle**: append-only.

### 5.13 ExportJob
- **Purpose**: tracks deterministic generation of flattened outputs.
- **Key fields**: `id`, `revisionId`, `profile`, `status`, `requestedBy`, `requestedAt`, `completedAt?`, `outputPath?`, `inputSnapshotHash`.
- **Relationships**: belongs to `DocumentRevision`; generates derived files.
- **Lifecycle**: `queued -> running -> succeeded|failed|cancelled`.

---

## 6. Data flow design

### 6.1 Import/open a PDF
1. User selects file in desktop UI.
2. Tauri command copies file to managed workspace path, computes checksum.
3. Renderer opens file for metadata/page count extraction.
4. Persistence transaction creates/updates `Document` + inserts `DocumentRevision`.
5. Audit event appended (`document_revision_imported`).

**Storage placement**
- SQLite: document + revision metadata + audit.
- Local files: source PDF.
- In-memory: opened renderer handle and initial page cache entries.

### 6.2 Render a page
1. Viewer requests page render from `RendererProvider` with viewport/tile spec.
2. Adapter serves from cache or schedules raster job.
3. Rendered surface returned to viewer and painted.
4. Overlay engine draws markups/comments from in-memory revision snapshot.

**Storage placement**
- In-memory caches: raster tiles, viewport state.
- Renderer layer: document/page handles.
- SQLite: no write path for pure render.

### 6.3 Create a markup
1. User draws object in overlay layer (page coordinates).
2. Markup core validates geometry and snaps to model constraints.
3. Transaction inserts `MarkupObject` and `AuditEvent`.
4. UI updates overlay state and index structures.

**Storage placement**
- SQLite: markup row + audit event.
- In-memory: overlay scene graph and spatial index.

### 6.4 Update a markup
1. User edits geometry/style/status.
2. Markup core computes patch + validation.
3. Transaction updates `MarkupObject` and inserts `AuditEvent`.
4. Overlay redraws changed object only.

### 6.5 Attach comment thread to markup
1. User opens comment panel on markup.
2. Transaction creates `CommentThread`, first `Comment`, and `AuditEvent`.
3. UI links thread badge to markup anchor.

**Storage placement**
- SQLite: thread/comment/audit.
- In-memory: thread panel cache.

### 6.6 Resolve/reopen markup issue
1. Status change requested from markup or thread context.
2. Domain rule check (e.g., unresolved mandatory confirmations may block resolve).
3. Transaction updates status fields and appends audit entry.
4. Workflow filters refresh counts and lists.

### 6.7 Assign reviewer
1. Workflow UI creates assignment request.
2. Transaction inserts `ReviewerAssignment` + optional `Reminder` seed + `AuditEvent`.
3. Work queue view refreshes for assignee.

### 6.8 Confirm squad check
1. Reviewer submits check result and confirmation decision.
2. Transaction updates `SquadCheck`, inserts `Confirmation`, and `AuditEvent`.
3. Dependent workflow states recomputed (e.g., revision review gate conditions).

### 6.9 Export marked-up PDF
1. User creates `ExportJob` with profile.
2. Export engine snapshots relevant entities from SQLite.
3. Renderer loads source revision PDF and applies flattening instructions.
4. Output file written to exports directory; job status updated.
5. Audit event appended.

**Storage placement**
- SQLite: export job status + audit.
- Local files: generated PDF and optional JSON/report.
- Renderer layer: transient render/write context.
- Future sync service: publish export manifest and hashes only when enabled.

---

## 7. Repo refactor plan

### 7.1 Target structure

```text
GITPLANT/
  apps/
    desktop/
      src/
        app/
        features/
          workspace/
          viewer/
          markup/
          comments/
          workflow/
        infrastructure/
          renderer-client/
          persistence-client/
      src-tauri/
        src/
          commands/
          services/
          db/
          fs/
          export/
  packages/
    shared-types/
      src/
        domain/
        renderer/
        workflow/
        audit/
    viewer-core/
      src/
        contracts/
        viewport/
        cache/
        controller/
    viewer-pdfjs/
      src/
        PdfjsRendererProvider.ts
        transforms/
        text/
    markup-core/
      src/
        models/
        tools/
        rules/
    workflow-core/
      src/
        models/
        transitions/
        services/
    persistence-sqlite/
      src/
        repositories/
        migrations/
        unit-of-work/
    export-core/
      src/
        pipeline/
        profiles/
        flattening/
  docs/
    PDF_REVIEW_ARCHITECTURE_PACKAGE.md
    MIGRATION_PLAN_DESKTOP_FIRST.md
```

### 7.2 Why this structure supports growth and renderer swap

- `viewer-core` depends only on renderer contracts, never PDF.js.
- `viewer-pdfjs` is replaceable by `viewer-native` with parallel contract tests.
- `markup-core` and `workflow-core` are independently testable and reusable.
- Tauri backend concerns (SQLite/file/export/security) remain isolated from UI.
- Shared types prevent drift between Rust commands, TS UI, and package modules.

---

## 8. Phased implementation roadmap

### Phase 1: Desktop foundation + review core

**Goals**
- Tauri desktop shell operational.
- PDF open/view through renderer abstraction.
- SQLite schema + repositories.
- Markup overlay model.
- Comment threads.
- Audit log append for state changes.

**Dependencies**
- Baseline repo refactor complete.
- Shared contracts finalized.
- Initial migration set for core entities.

**Done criteria**
- Open large PDF locally and navigate pages smoothly.
- Create/update/resolve markup and comment thread with persisted state.
- Restart app and recover full local review state.
- Audit events generated for core operations.

**Risks**
- Early coupling to PDF.js internals in UI.
- Unbounded memory from naive raster caching.
- SQLite transaction boundaries not aligned to domain operations.

### Phase 2: Workflow execution layer

**Goals**
- Reviewer assignment system.
- Squad check flow.
- Confirmations and reminders.
- Status filtering and dashboard views.

**Dependencies**
- Stable identity/user model for local actors.
- Workflow transition rules in core package.

**Done criteria**
- Assign reviewers and track completion state.
- Execute squad checks with confirmations and audit trace.
- Reminder scheduling and acknowledgement lifecycle functional.

**Risks**
- Workflow complexity growth without explicit state machine tests.
- Reminder delivery UX unclear in offline-only sessions.

### Phase 3: Export + performance hardening + collaboration path

**Goals**
- Export engine for flattened PDFs and structured review bundles.
- Advanced performance tuning (tile cache policy, prefetch heuristics).
- Sync/collaboration architecture scaffolding.
- Optional native renderer proof-of-path.

**Dependencies**
- Stable domain schema and workflow states.
- Renderer contract test suite.

**Done criteria**
- Deterministic exports with traceable job records.
- Measured performance targets met on representative large engineering PDFs.
- Sync interfaces defined and local event log suitable for replication.
- Native renderer feasibility validated without app-wide refactor.

**Risks**
- Export fidelity differences across renderer implementations.
- Cross-platform packaging/signing constraints.
- Scope creep into real-time collaboration before local robustness.

---

## 9. Recommended immediate next coding step

**Next step**: implement the **contract-only foundation** (no feature expansion yet):
1. Create `packages/shared-types` with renderer/domain/workflow type contracts.
2. Create `packages/viewer-core` with `RendererProvider` interface and contract tests.
3. Create `packages/viewer-pdfjs` minimal adapter stub implementing the interface for open/count/render metadata smoke tests.
4. Add architecture decision records (ADRs) for local-first data authority and renderer swappability.

This is the smallest coding slice that locks architectural boundaries before feature implementation.

# Desktop-First Product Architecture Blueprint (Updated)

This blueprint is updated to align with `docs/PDF_REVIEW_ARCHITECTURE_PACKAGE.md` and ADR-0002.

## Core extension points now locked in

- Renderer abstraction layer (`viewer-core`)
- PDF.js adapter (`viewer-pdfjs`)
- Future native renderer adapter slot (same contract)
- Document transformation engine boundary
- OCR/indexing processing pipeline boundary
- Multi-layer render scene model
- Persistence for derived revisions, processing jobs, extracted page text, and audit events

## Domain essentials

- `Document` stable identity
- `DocumentRevision` immutable snapshots with `source_revision_id` and `derivation_type`
- `DocumentTransformationJob` (command + result, audit-linked)
- `ProcessingJob` (`text_extraction|ocr|thumbnail_generation|export`)
- `ExtractedPageText` page-addressable text content
- `ComparisonSession` base + optional overlay revision state
- `AuditEvent` for transformation/processing traceability

## Architectural guardrails

1. Viewer/UI code must not directly import PDF.js internals.
2. Transform operations must create new revisions (no in-place mutation).
3. OCR and text extraction are processing concerns, not rendering concerns.
4. Originals remain immutable in managed local storage.

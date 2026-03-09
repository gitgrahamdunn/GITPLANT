# ADR 0002: Multi-layer viewer + transformation engine + processing pipeline boundaries

## Status
Accepted

## Context
The desktop-first baseline already separates renderer infrastructure from product-domain behavior, but Pass 2 requires explicit support for derived revisions, processing jobs, and comparison-ready page layering before deeper features are implemented.

## Decision
1. **PDF rendering stays infrastructure**
   - Rendering remains behind `viewer-core` contracts.
   - `viewer-pdfjs` is an adapter; future native renderer is another adapter slot.
2. **Markup/workflow stay product-core**
   - Markup, comments, reviewer workflow, confirmations, and audit remain in domain/persistence services, not renderer code.
3. **Document transformations are a dedicated engine**
   - Transform operations are modeled as commands (`delete_pages`, `insert_pages`, `reorder_pages`, `extract_pages`, `combine_documents`).
   - Viewer is read-only and never mutates source files.
4. **OCR/indexing is a processing pipeline**
   - Processing jobs are tracked independently from rendering.
   - `text_extraction` and `ocr` are distinct job types.
5. **Viewer supports stacked layers from day one**
   - Render scenes include multiple `RenderLayer` records (`base_pdf`, `overlay_pdf`, future markup/selection layers).
6. **Originals are immutable**
   - Imported revisions are immutable.
   - Transformations create derived `DocumentRevision` rows with `source_revision_id`.

## Consequences
- Existing Pass 1 flow still works while enabling comparison, text search, and transform jobs without architecture rewrites.
- SQLite schema now stores revision lineage, processing jobs, extracted page text, and audit events for transform/processing actions.

import { invoke } from '@tauri-apps/api/core';
import type { PersistenceGateway, ImportedDocumentPayload, DerivedRevisionPayload } from '@gitplant/persistence-core';
import type { ExtractedPageTextRecord, ProcessingJobRecord, RecentDocumentView } from '@gitplant/shared-types';

export const tauriGateway: PersistenceGateway = {
  importPdfFromPicker: () => invoke<ImportedDocumentPayload>('import_pdf_from_picker'),
  listRecentDocuments: () => invoke<RecentDocumentView[]>('list_recent_documents'),
  openDocument: (documentId: string) => invoke<ImportedDocumentPayload>('open_document', { documentId }),
  readDocumentBytes: (documentId: string, revisionId?: string) => invoke<number[]>('read_document_bytes', { documentId, revisionId }),
  updatePageCount: (revisionId: string, pageCount: number) => invoke<void>('update_page_count', { revisionId, pageCount }),
  extractPagesToDerivedRevision: (revisionId: string, startPage: number, endPage: number) =>
    invoke<DerivedRevisionPayload>('extract_pages_to_derived_revision', { revisionId, startPage, endPage }),
  triggerTextExtraction: (revisionId: string) => invoke<ProcessingJobRecord>('trigger_text_extraction', { revisionId }),
  listExtractedPageText: (revisionId: string) => invoke<ExtractedPageTextRecord[]>('list_extracted_page_text', { revisionId })
};

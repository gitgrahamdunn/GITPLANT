import { invoke } from '@tauri-apps/api/core';
import type { PersistenceGateway, ImportedDocumentPayload, DerivedRevisionPayload } from '@gitplant/persistence-core';
import type { ExtractedPageTextRecord, ProcessingJobRecord, RecentDocumentView } from '@gitplant/shared-types';

const isTauriRuntime = (): boolean => typeof window !== 'undefined' && '__TAURI_INTERNALS__' in window;

async function invokeOrFallback<T>(command: string, args?: Record<string, unknown>): Promise<T> {
  if (isTauriRuntime()) {
    return invoke<T>(command, args);
  }

  switch (command) {
    case 'list_recent_documents':
      return [] as T;
    case 'list_extracted_page_text':
      return [] as T;
    default:
      throw new Error(`Tauri command unavailable in browser test mode: ${command}`);
  }
}

export const tauriGateway: PersistenceGateway = {
  importPdfFromPicker: () => invokeOrFallback<ImportedDocumentPayload>('import_pdf_from_picker'),
  listRecentDocuments: () => invokeOrFallback<RecentDocumentView[]>('list_recent_documents'),
  openDocument: (documentId: string) => invokeOrFallback<ImportedDocumentPayload>('open_document', { documentId }),
  readDocumentBytes: (documentId: string, revisionId?: string) => invokeOrFallback<number[]>('read_document_bytes', { documentId, revisionId }),
  updatePageCount: (revisionId: string, pageCount: number) => invokeOrFallback<void>('update_page_count', { revisionId, pageCount }),
  extractPagesToDerivedRevision: (revisionId: string, startPage: number, endPage: number) =>
    invokeOrFallback<DerivedRevisionPayload>('extract_pages_to_derived_revision', { revisionId, startPage, endPage }),
  triggerTextExtraction: (revisionId: string) => invokeOrFallback<ProcessingJobRecord>('trigger_text_extraction', { revisionId }),
  listExtractedPageText: (revisionId: string) => invokeOrFallback<ExtractedPageTextRecord[]>('list_extracted_page_text', { revisionId })
};

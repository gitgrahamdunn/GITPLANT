import { invoke } from '@tauri-apps/api/core';
import type { PersistenceGateway, ImportedDocumentPayload } from '@gitplant/persistence-core';
import type { RecentDocumentView } from '@gitplant/shared-types';

export const tauriGateway: PersistenceGateway = {
  importPdfFromPicker: () => invoke<ImportedDocumentPayload>('import_pdf_from_picker'),
  listRecentDocuments: () => invoke<RecentDocumentView[]>('list_recent_documents'),
  openDocument: (documentId: string) => invoke<ImportedDocumentPayload>('open_document', { documentId }),
  readDocumentBytes: (documentId: string) => invoke<number[]>('read_document_bytes', { documentId }),
  updatePageCount: (documentId: string, pageCount: number) => invoke<void>('update_page_count', { documentId, pageCount })
};

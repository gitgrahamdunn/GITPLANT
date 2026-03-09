import type { RecentDocumentView } from '@gitplant/shared-types';

export interface ImportedDocumentPayload {
  documentId: string;
  title: string;
  managedFilePath: string;
  fileSizeBytes: number;
}

export interface PersistenceGateway {
  importPdfFromPicker(): Promise<ImportedDocumentPayload>;
  listRecentDocuments(): Promise<RecentDocumentView[]>;
  openDocument(documentId: string): Promise<ImportedDocumentPayload>;
  readDocumentBytes(documentId: string): Promise<number[]>;
  updatePageCount(documentId: string, pageCount: number): Promise<void>;
}

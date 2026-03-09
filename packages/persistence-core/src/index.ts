import type {
  ProcessingJobRecord,
  ExtractedPageTextRecord,
  RecentDocumentView
} from '@gitplant/shared-types';

export interface ImportedDocumentPayload {
  documentId: string;
  title: string;
  managedFilePath: string;
  fileSizeBytes: number;
  revisionId: string;
}

export interface DerivedRevisionPayload {
  documentId: string;
  sourceRevisionId: string;
  derivedRevisionId: string;
  managedFilePath: string;
  pageCount: number;
}

export interface PersistenceGateway {
  importPdfFromPicker(): Promise<ImportedDocumentPayload>;
  listRecentDocuments(): Promise<RecentDocumentView[]>;
  openDocument(documentId: string): Promise<ImportedDocumentPayload>;
  readDocumentBytes(documentId: string, revisionId?: string): Promise<number[]>;
  updatePageCount(revisionId: string, pageCount: number): Promise<void>;
  extractPagesToDerivedRevision(revisionId: string, startPage: number, endPage: number): Promise<DerivedRevisionPayload>;
  triggerTextExtraction(revisionId: string): Promise<ProcessingJobRecord>;
  listExtractedPageText(revisionId: string): Promise<ExtractedPageTextRecord[]>;
}

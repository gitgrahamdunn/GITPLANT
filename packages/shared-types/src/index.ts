export interface DocumentRecord {
  id: string;
  title: string;
  createdAt: string;
  updatedAt: string;
}

export type DerivationType =
  | 'imported_original'
  | 'extract_pages'
  | 'combine_documents'
  | 'delete_pages'
  | 'insert_pages'
  | 'reorder_pages';

export interface DocumentRevisionRecord {
  id: string;
  documentId: string;
  managedFilePath: string;
  originalFileName: string;
  pageCount?: number | null;
  fileSizeBytes: number;
  importedAt: string;
  sourceRevisionId?: string | null;
  derivationType?: DerivationType | null;
}

export interface RecentDocumentRecord {
  id: string;
  documentId: string;
  openedAt: string;
}

export interface RecentDocumentView {
  documentId: string;
  title: string;
  managedFilePath: string;
  openedAt: string;
  pageCount?: number | null;
  activeRevisionId?: string;
}

export type ProcessingJobType = 'text_extraction' | 'ocr' | 'thumbnail_generation' | 'export';
export type ProcessingJobStatus = 'pending' | 'running' | 'completed' | 'failed';

export interface ProcessingJobRecord {
  id: string;
  revisionId: string;
  jobType: ProcessingJobType;
  status: ProcessingJobStatus;
  payloadJson?: string | null;
  errorMessage?: string | null;
  createdAt: string;
  startedAt?: string | null;
  completedAt?: string | null;
}

export interface ExtractedPageTextRecord {
  id: string;
  revisionId: string;
  pageNumber: number;
  textContent: string;
  extractedAt: string;
}

export interface ComparisonSession {
  baseRevisionId: string;
  overlayRevisionId?: string;
  pageNumber: number;
}

export interface AuditEvent {
  id: string;
  entityType: string;
  entityId: string;
  eventType: string;
  payloadJson?: string | null;
  occurredAt: string;
}

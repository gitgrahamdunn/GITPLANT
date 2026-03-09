export interface DocumentRecord {
  id: string;
  title: string;
  createdAt: string;
  updatedAt: string;
}

export interface DocumentRevisionRecord {
  id: string;
  documentId: string;
  revisionNumber: number;
  managedFilePath: string;
  originalFileName: string;
  sourcePath?: string | null;
  pageCount?: number | null;
  fileSizeBytes: number;
  importedAt: string;
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
}

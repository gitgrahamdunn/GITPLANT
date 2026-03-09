export type TransformationKind =
  | 'delete_pages'
  | 'insert_pages'
  | 'reorder_pages'
  | 'extract_pages'
  | 'combine_documents';

export interface TransformationRequest {
  kind: TransformationKind;
  sourceRevisionId: string;
  payload: Record<string, unknown>;
}

export interface TransformationResult {
  documentId: string;
  sourceRevisionId: string;
  derivedRevisionId: string;
  managedFilePath: string;
  pageCount: number;
}

export interface DocumentTransformEngine {
  run(request: TransformationRequest): Promise<TransformationResult>;
}

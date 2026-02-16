export type Role = 'user';

export interface LoginResponse {
  access_token: string;
  token_type: string;
  role: Role;
}

export interface MeResponse {
  email: string;
  role: Role;
}

export interface DashboardSummary {
  total_documents: number;
  documents_ifa: number;
  documents_ifc: number;
  open_approvals: number;
  total_transmittals: number;
}

export interface SearchDocument {
  id: number;
  project_code: string;
  document_number: string;
  title: string;
  discipline: string;
  status: string;
  current_revision: string;
}

export interface DocumentSearchResponse {
  total: number;
  items: SearchDocument[];
}

export interface DocumentCreateRequest {
  project_code: string;
  document_number: string;
  title: string;
  discipline: string;
}


export interface DocumentBatchCreateResponse {
  total_created: number;
  items: SearchDocument[];
}

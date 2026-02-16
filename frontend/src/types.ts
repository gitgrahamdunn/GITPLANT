export type Role = 'document_controller' | 'engineer' | 'approver';

export interface LoginResponse {
  access_token: string;
  token_type: string;
  role: string;
}

export interface MeResponse {
  email: string;
  role: string;
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
  doc_number: string;
  title: string;
  discipline: string;
  current_status: string;
}

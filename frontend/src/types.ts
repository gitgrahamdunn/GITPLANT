export type Role = 'viewer' | 'engineer' | 'approver' | 'admin';

export interface LoginResponse {
  access_token: string;
  token_type: string;
}

export interface MeResponse {
  user_id: number;
  username: string;
  role: Role;
}

export interface DashboardSummary {
  total_documents: number;
  by_status: Record<string, number>;
  open_transmittals: number;
  approvals_pending: number;
}

export interface SearchDocument {
  id: number;
  doc_number: string;
  title: string;
  discipline: string;
  current_status: string;
}

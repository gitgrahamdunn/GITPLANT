export type Role = "user";

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
  active_project_count?: number;
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

export interface PullForRevisionResponse {
  document_id: number;
  document_number: string;
  message: string;
  download_url: string;
}

export interface DemoSeedResponse {
  status: string;
  documents_created: number;
  approvals_created: number;
  audits_created: number;
  warning: string;
}

export interface ProjectSummary {
  id: string;
  project_number: string;
  name: string | null;
  description: string | null;
  status: string;
  created_by: string;
  created_at: string;
  working_doc_count: number;
}

export interface ProjectCreateRequest {
  project_number: string;
  name?: string;
  description?: string;
}

export interface ProjectWorkingDoc {
  id: number;
  project_id: string;
  document_id: number;
  document_number: string;
  title: string;
  current_plant_revision: string;
  working_revision_label: string;
  status: "WORKING" | "READY" | "MERGED" | "ABANDONED";
  pulled_by: string;
  created_at: string;
  updated_at: string;
}

export interface ProjectDetail {
  id: string;
  project_number: string;
  name: string | null;
  description: string | null;
  status: string;
  created_by: string;
  created_at: string;
  working_docs: ProjectWorkingDoc[];
}

export interface ProjectPullResponse {
  project_number: string;
  created: ProjectWorkingDoc[];
  skipped_document_ids: number[];
}

export interface WorkingRevisionStatusResponse {
  id: number;
  status: string;
  updated_at: string;
}

export interface ProjectWorkingUploadResponse {
  id: number;
  file_path: string;
  updated_at: string;
}

export interface ProjectMergeItem {
  working_revision_id: number;
  document_id: number;
  document_number: string;
  previous_revision: string;
  new_revision: string;
}

export interface ProjectMergeResponse {
  project_number: string;
  merged_count: number;
  merged_items: ProjectMergeItem[];
}

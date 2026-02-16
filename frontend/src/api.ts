import type {
  DemoSeedResponse,
  DocumentBatchCreateResponse,
  DocumentCreateRequest,
  DocumentSearchResponse,
  LoginResponse,
  MeResponse,
  DashboardSummary,
  ProjectCreateRequest,
  ProjectDetail,
  ProjectMergeResponse,
  ProjectPullResponse,
  ProjectSummary,
  ProjectWorkingUploadResponse,
  PullForRevisionResponse,
  SearchDocument,
  WorkingRevisionStatusResponse,
} from "./types";

const API_BASE_URL =
  (import.meta as ImportMeta & { env?: Record<string, string | undefined> }).env
    ?.VITE_API_BASE_URL ?? "http://localhost:8000";

function getAuthHeaders(token: string): HeadersInit {
  return { Authorization: `Bearer ${token}` };
}

function buildApiUrl(path: string): string {
  return `${API_BASE_URL}${path}`;
}

function formatErrorPayload(payload: unknown, fallback: string): string {
  if (!payload || typeof payload !== "object") {
    return fallback;
  }

  const detail = (payload as { detail?: unknown }).detail;
  if (typeof detail === "string") {
    return detail;
  }

  if (Array.isArray(detail)) {
    const messages = detail
      .map((item) =>
        typeof item === "object" && item && "msg" in item
          ? String(item.msg)
          : null,
      )
      .filter(Boolean);

    if (messages.length) {
      return messages.join(", ");
    }
  }

  return fallback;
}

async function requestForm<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const response = await fetch(buildApiUrl(path), options);

  if (!response.ok) {
    let message = `Request failed with ${response.status}`;
    const contentType = response.headers.get("content-type") ?? "";

    if (contentType.includes("application/json")) {
      const payload = await response.json();
      message = formatErrorPayload(payload, message);
    } else {
      const text = await response.text();
      if (text) {
        message = text;
      }
    }

    throw new Error(message);
  }

  return response.json() as Promise<T>;
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(buildApiUrl(path), {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers ?? {}),
    },
    ...options,
  });

  if (!response.ok) {
    let message = `Request failed with ${response.status}`;
    const contentType = response.headers.get("content-type") ?? "";

    if (contentType.includes("application/json")) {
      const payload = await response.json();
      message = formatErrorPayload(payload, message);
    } else {
      const text = await response.text();
      if (text) {
        message = text;
      }
    }

    throw new Error(message);
  }

  return response.json() as Promise<T>;
}

export async function login(
  email: string,
  password: string,
): Promise<LoginResponse> {
  return request<LoginResponse>("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

export async function fetchDashboard(
  token: string,
): Promise<DashboardSummary> {
  return request<DashboardSummary>("/documents/reports/dashboard-summary", {
    headers: {
      ...getAuthHeaders(token),
    },
  });
}

export async function fetchMe(token: string): Promise<MeResponse> {
  return request<MeResponse>("/auth/me", {
    headers: {
      ...getAuthHeaders(token),
    },
  });
}

export async function createDocument(
  token: string,
  payload: DocumentCreateRequest,
): Promise<SearchDocument> {
  return request<SearchDocument>("/documents", {
    method: "POST",
    headers: {
      ...getAuthHeaders(token),
    },
    body: JSON.stringify(payload),
  });
}

export async function listDocuments(
  token: string,
): Promise<DocumentSearchResponse> {
  return request<DocumentSearchResponse>("/documents", {
    headers: {
      ...getAuthHeaders(token),
    },
  });
}

export async function searchDocuments(
  token: string,
  query: string,
): Promise<DocumentSearchResponse> {
  const params = new URLSearchParams();
  if (query.trim()) {
    params.set("q", query.trim());
  }

  const suffix = params.toString() ? `?${params.toString()}` : "";

  return request<DocumentSearchResponse>(`/documents/search${suffix}`, {
    headers: {
      ...getAuthHeaders(token),
    },
  });
}

export async function uploadPdfDocuments(
  token: string,
  payload: FormData,
): Promise<DocumentBatchCreateResponse> {
  return requestForm<DocumentBatchCreateResponse>("/documents/upload-pdf", {
    method: "POST",
    headers: {
      ...getAuthHeaders(token),
    },
    body: payload,
  });
}

export async function uploadPlantRevision(
  token: string,
  documentId: number,
  file: File,
): Promise<SearchDocument> {
  const payload = new FormData();
  payload.append("file", file, file.name);

  return requestForm<SearchDocument>(`/documents/${documentId}/plant/upload`, {
    method: "POST",
    headers: {
      ...getAuthHeaders(token),
    },
    body: payload,
  });
}

export async function pullDocumentForRevision(
  token: string,
  documentId: number,
): Promise<PullForRevisionResponse> {
  return request<PullForRevisionResponse>(
    `/documents/${documentId}/pull-for-revision`,
    {
      method: "POST",
      headers: getAuthHeaders(token),
    },
  );
}

export async function downloadDocumentPdf(
  token: string,
  documentId: number,
): Promise<Blob> {
  const response = await fetch(buildApiUrl(`/documents/${documentId}/download`), {
    headers: getAuthHeaders(token),
  });

  if (!response.ok) {
    let message = `Request failed with ${response.status}`;
    const contentType = response.headers.get("content-type") ?? "";

    if (contentType.includes("application/json")) {
      const payload = await response.json();
      message = formatErrorPayload(payload, message);
    } else {
      const text = await response.text();
      if (text) {
        message = text;
      }
    }

    throw new Error(message);
  }

  return response.blob();
}

export async function createProject(
  token: string,
  payload: ProjectCreateRequest,
): Promise<ProjectSummary> {
  return request<ProjectSummary>("/projects", {
    method: "POST",
    headers: { ...getAuthHeaders(token) },
    body: JSON.stringify(payload),
  });
}

export async function listProjects(
  token: string,
  status?: string,
): Promise<ProjectSummary[]> {
  const suffix = status ? `?status=${encodeURIComponent(status)}` : "";
  return request<ProjectSummary[]>(`/projects${suffix}`, {
    headers: { ...getAuthHeaders(token) },
  });
}

export async function getProjectDetail(
  token: string,
  projectNumber: string,
): Promise<ProjectDetail> {
  return request<ProjectDetail>(`/projects/${projectNumber}`, {
    headers: { ...getAuthHeaders(token) },
  });
}

export async function pullDocumentsForProject(
  token: string,
  projectId: string,
  documentIds: number[],
): Promise<ProjectPullResponse> {
  return request<ProjectPullResponse>(`/projects/${projectId}/pull`, {
    method: "POST",
    headers: { ...getAuthHeaders(token) },
    body: JSON.stringify({ document_ids: documentIds }),
  });
}

export async function uploadProjectWorkingRevision(
  token: string,
  projectId: string,
  workingRevisionId: number,
  file: File,
): Promise<ProjectWorkingUploadResponse> {
  const payload = new FormData();
  payload.append("file", file, file.name);

  return requestForm<ProjectWorkingUploadResponse>(
    `/projects/${projectId}/working/${workingRevisionId}/upload`,
    {
      method: "POST",
      headers: { ...getAuthHeaders(token) },
      body: payload,
    },
  );
}

export async function markWorkingReady(
  token: string,
  projectNumber: string,
  workingRevisionId: number,
): Promise<WorkingRevisionStatusResponse> {
  return request<WorkingRevisionStatusResponse>(
    `/projects/${projectNumber}/working/${workingRevisionId}/ready`,
    {
      method: "POST",
      headers: { ...getAuthHeaders(token) },
    },
  );
}

export async function abandonWorkingRevision(
  token: string,
  projectNumber: string,
  workingRevisionId: number,
): Promise<WorkingRevisionStatusResponse> {
  return request<WorkingRevisionStatusResponse>(
    `/projects/${projectNumber}/working/${workingRevisionId}/abandon`,
    {
      method: "POST",
      headers: { ...getAuthHeaders(token) },
    },
  );
}

export async function mergeProjectToPlant(
  token: string,
  projectNumber: string,
): Promise<ProjectMergeResponse> {
  return request<ProjectMergeResponse>(`/projects/${projectNumber}/merge`, {
    method: "POST",
    headers: { ...getAuthHeaders(token) },
  });
}

export async function seedDemoData(token: string): Promise<DemoSeedResponse> {
  return request<DemoSeedResponse>("/documents/admin/dev/seed-demo", {
    method: "POST",
    headers: {
      ...getAuthHeaders(token),
    },
  });
}

export async function resetDemoData(token: string): Promise<DemoSeedResponse> {
  return request<DemoSeedResponse>("/documents/admin/dev/reset-demo", {
    method: "POST",
    headers: {
      ...getAuthHeaders(token),
    },
  });
}

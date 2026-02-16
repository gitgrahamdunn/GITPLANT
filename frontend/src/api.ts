import type {
  DashboardSummary,
  DocumentBatchCreateResponse,
  DocumentCreateRequest,
  DocumentSearchResponse,
  LoginResponse,
  MeResponse,
  PullForRevisionResponse,
  SearchDocument
} from './types';

const API_BASE_URL =
  (import.meta as ImportMeta & { env?: Record<string, string | undefined> }).env
    ?.VITE_API_BASE_URL ?? 'http://localhost:8000';

function getAuthHeaders(token: string): HeadersInit {
  return { Authorization: `Bearer ${token}` };
}

function buildApiUrl(path: string): string {
  return `${API_BASE_URL}${path}`;
}

function formatErrorPayload(payload: unknown, fallback: string): string {
  if (!payload || typeof payload !== 'object') {
    return fallback;
  }

  const detail = (payload as { detail?: unknown }).detail;
  if (typeof detail === 'string') {
    return detail;
  }

  if (Array.isArray(detail)) {
    const messages = detail
      .map((item) => (typeof item === 'object' && item && 'msg' in item ? String(item.msg) : null))
      .filter(Boolean);

    if (messages.length) {
      return messages.join(', ');
    }
  }

  return fallback;
}



async function requestForm<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(buildApiUrl(path), options);

  if (!response.ok) {
    let message = `Request failed with ${response.status}`;
    const contentType = response.headers.get('content-type') ?? '';

    if (contentType.includes('application/json')) {
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
      'Content-Type': 'application/json',
      ...(options.headers ?? {})
    },
    ...options
  });

  if (!response.ok) {
    let message = `Request failed with ${response.status}`;
    const contentType = response.headers.get('content-type') ?? '';

    if (contentType.includes('application/json')) {
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

export async function login(email: string, password: string): Promise<LoginResponse> {
  return request<LoginResponse>('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password })
  });
}

export async function fetchMe(token: string): Promise<MeResponse> {
  return request<MeResponse>('/auth/me', {
    headers: {
      ...getAuthHeaders(token)
    }
  });
}

export async function fetchDashboard(token: string): Promise<DashboardSummary> {
  return request<DashboardSummary>('/documents/reports/dashboard-summary', {
    headers: {
      ...getAuthHeaders(token)
    }
  });
}



export async function createDocument(
  token: string,
  payload: DocumentCreateRequest
): Promise<SearchDocument> {
  return request<SearchDocument>('/documents', {
    method: 'POST',
    headers: {
      ...getAuthHeaders(token)
    },
    body: JSON.stringify(payload)
  });
}
export async function searchDocuments(
  token: string,
  query: string
): Promise<DocumentSearchResponse> {
  const params = new URLSearchParams();
  if (query.trim()) {
    params.set('q', query.trim());
  }

  const suffix = params.toString() ? `?${params.toString()}` : '';

  return request<DocumentSearchResponse>(`/documents/search${suffix}`, {
    headers: {
      ...getAuthHeaders(token)
    }
  });
}


export async function uploadPdfDocuments(
  token: string,
  payload: FormData
): Promise<DocumentBatchCreateResponse> {
  return requestForm<DocumentBatchCreateResponse>('/documents/upload-pdf', {
    method: 'POST',
    headers: {
      ...getAuthHeaders(token)
    },
    body: payload
  });
}


export async function pullDocumentForRevision(
  token: string,
  documentId: number
): Promise<PullForRevisionResponse> {
  return request<PullForRevisionResponse>(`/documents/${documentId}/pull-for-revision`, {
    method: 'POST',
    headers: getAuthHeaders(token)
  });
}

export function getDocumentDownloadUrl(documentId: number): string {
  return buildApiUrl(`/documents/${documentId}/download`);
}


export async function downloadDocumentPdf(token: string, documentId: number): Promise<Blob> {
  const response = await fetch(buildApiUrl(`/documents/${documentId}/download`), {
    headers: getAuthHeaders(token)
  });

  if (!response.ok) {
    let message = `Request failed with ${response.status}`;
    const contentType = response.headers.get('content-type') ?? '';

    if (contentType.includes('application/json')) {
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

import type {
  DashboardSummary,
  LoginResponse,
  MeResponse,
  Role,
  SearchDocument
} from './types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000';

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers ?? {})
    },
    ...options
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `Request failed with ${response.status}`);
  }

  return response.json() as Promise<T>;
}

export async function login(username: string, role: Role): Promise<LoginResponse> {
  return request<LoginResponse>('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ username, role })
  });
}

export async function fetchMe(token: string): Promise<MeResponse> {
  return request<MeResponse>('/auth/me', {
    headers: {
      Authorization: `Bearer ${token}`
    }
  });
}

export async function fetchDashboard(token: string): Promise<DashboardSummary> {
  return request<DashboardSummary>('/documents/reports/dashboard', {
    headers: {
      Authorization: `Bearer ${token}`
    }
  });
}

export async function searchDocuments(token: string, query: string): Promise<SearchDocument[]> {
  const params = new URLSearchParams();
  if (query.trim()) {
    params.set('q', query.trim());
  }

  const suffix = params.toString() ? `?${params.toString()}` : '';

  return request<SearchDocument[]>(`/documents/search${suffix}`, {
    headers: {
      Authorization: `Bearer ${token}`
    }
  });
}

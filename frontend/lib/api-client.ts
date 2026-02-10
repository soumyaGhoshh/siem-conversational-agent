import { useAppStore } from './store';
import type {
  PreflightStatus,
  Schema,
  ChatResponse,
  AuditEntry,
  SavedSearch,
  TimeRange,
  QueryOperator,
} from './types';

const API_BASE = 'http://127.0.0.1:8000/api';

const getHeaders = (accessToken?: string) => {
  const token = accessToken || useAppStore.getState().user?.accessToken;
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  return headers;
};

const handleResponse = async (res: Response) => {
  if (res.status === 401) {
    // Unauthorized - clear store and redirect to login
    if (typeof window !== 'undefined') {
      window.location.href = '/login';
    }
    throw new Error('Unauthorized');
  }
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: 'Request failed' }));
    throw new Error(error.detail || 'Request failed');
  }
  return res.json();
};

export const apiClient = {
  async getPreflight(): Promise<PreflightStatus> {
    const res = await fetch(`${API_BASE}/preflight`);
    return handleResponse(res);
  },

  async getSchema(index: string, accessToken?: string): Promise<Schema> {
    const res = await fetch(`${API_BASE}/schema?index=${index}`, {
      headers: getHeaders(accessToken),
    });
    return handleResponse(res);
  },

  async chat(
    prompt: string,
    index: string,
    size: number,
    accessToken?: string
  ): Promise<ChatResponse> {
    const res = await fetch(`${API_BASE}/chat`, {
      method: 'POST',
      headers: getHeaders(accessToken),
      body: JSON.stringify({ prompt, index, size }),
    });
    return handleResponse(res);
  },

  async buildQuery(
    field: string,
    op: QueryOperator,
    value: string | number,
    timeRange: TimeRange,
    size: number,
    index: string,
    accessToken?: string
  ): Promise<ChatResponse> {
    const res = await fetch(`${API_BASE}/builder`, {
      method: 'POST',
      headers: getHeaders(accessToken),
      body: JSON.stringify({ field, op, value, timeRange, size, index }),
    });
    return handleResponse(res);
  },

  async getAudit(accessToken?: string): Promise<AuditEntry[]> {
    const res = await fetch(`${API_BASE}/audit`, {
      headers: getHeaders(accessToken),
    });
    return handleResponse(res);
  },

  async getSavedSearches(accessToken?: string): Promise<SavedSearch[]> {
    const res = await fetch(`${API_BASE}/saved`, {
      headers: getHeaders(accessToken),
    });
    return handleResponse(res);
  },

  async getRecentAlerts(index: string, minLevel: number, accessToken?: string): Promise<any[]> {
    const res = await fetch(`${API_BASE}/alerts/recent?index=${index}&min_level=${minLevel}`, {
      headers: getHeaders(accessToken),
    });
    return handleResponse(res);
  },

  async createSavedSearch(
    name: string,
    index: string,
    queryJson: string,
    accessToken?: string
  ): Promise<SavedSearch> {
    const res = await fetch(`${API_BASE}/saved`, {
      method: 'POST',
      headers: getHeaders(accessToken),
      body: JSON.stringify({ name, index, queryJson }),
    });
    return handleResponse(res);
  },

  async runSavedSearch(id: number, accessToken?: string): Promise<ChatResponse> {
    const res = await fetch(`${API_BASE}/saved/run`, {
      method: 'POST',
      headers: getHeaders(accessToken),
      body: JSON.stringify({ id }),
    });
    return handleResponse(res);
  },

  async getStats(index: string, accessToken?: string): Promise<any> {
    const res = await fetch(`${API_BASE}/stats?index=${index}`, {
      headers: getHeaders(accessToken),
    });
    return handleResponse(res);
  },

  async getRecentAlerts(index: string, minLevel: number = 10, accessToken?: string): Promise<any[]> {
    const res = await fetch(`${API_BASE}/alerts/recent?index=${index}&min_level=${minLevel}`, {
      headers: getHeaders(accessToken),
    });
    return handleResponse(res);
  },

  async deleteSavedSearch(id: number, accessToken?: string): Promise<void> {
    const res = await fetch(`${API_BASE}/saved?id=${id}`, {
      method: 'DELETE',
      headers: getHeaders(accessToken),
    });
    return handleResponse(res);
  },
};

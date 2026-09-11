import type { ApplicationApiClient, ProjectRevision } from './applicationBoundary';

export function createHttpClient(baseUrl: string, fetcher: typeof fetch = fetch): ApplicationApiClient {
  const request = async <T>(path: string, init: RequestInit = {}): Promise<T> => {
    const response = await fetcher(`${baseUrl.replace(/\/$/, '')}${path}`, { ...init, headers: { 'content-type': 'application/json', ...(init.headers ?? {}) } });
    if (!response.ok) throw new Error(`ApplicationAPI request failed (${response.status})`);
    return response.status === 204 ? (undefined as T) : await response.json() as T;
  };
  return {
    createProject: input => request<ProjectRevision>('/projects', { method: 'POST', body: JSON.stringify(input) }),
    createRevision: (id, parent, input) => request<ProjectRevision>(`/projects/${encodeURIComponent(id)}/revisions`, { method: 'POST', headers: { 'if-match': parent }, body: JSON.stringify(input) }),
    preflight: (revision, requestBody) => request('/preflight', { method: 'POST', body: JSON.stringify({ revision_hash: revision, request: requestBody }) }),
    createRun: (key, preflight, requestBody) => request('/runs', { method: 'POST', headers: { 'idempotency-key': key }, body: JSON.stringify({ preflight_hash: preflight, request: requestBody }) }),
    getRun: id => request(`/runs/${encodeURIComponent(id)}`),
  };
}

/** ApplicationAPI boundary owned by S17; implementation is supplied by the generated client. */
export type ApiErrorCode = 'FIELD_UNSUPPORTED' | 'UNSAVED_CHANGES' | 'API_VALIDATION_ERROR' | 'REVISION_CONFLICT';
export type ApiError = { code: ApiErrorCode; message: string; pointer?: string };

export type ProjectRevision = { id: string; revision_hash: string; schema_version: string };
export type PreflightFinding = { severity: 'ERROR' | 'WARNING' | 'INFO'; message: string; pointer?: string };

export interface ApplicationApiClient {
  createProject(input: unknown): Promise<ProjectRevision>;
  createRevision(projectId: string, parentHash: string, input: unknown): Promise<ProjectRevision>;
  preflight(revisionHash: string, request: unknown): Promise<{ hash: string; findings: PreflightFinding[] }>;
  createRun(idempotencyKey: string, preflightHash: string, request: unknown): Promise<{ id: string }>;
  getRun(id: string): Promise<unknown>;
}

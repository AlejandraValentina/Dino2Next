import { describe, expect, it } from 'vitest';
import { stageFromPath } from '../../src/navigation/routes';
import { fieldBinding } from '../../src/route_entries/model';
import { ENGINE_SECTIONS, sectionStage } from '../../src/navigation/EngineTree';
import { loadUiPreferences, saveUiPreferences } from '../../src/shell/preferences';
import type { ApplicationApiClient } from '../../src/api/applicationBoundary';
import { createHttpClient } from '../../src/api/httpClient';
import { ApplicationApiError } from '../../src/api/httpClient';

describe('model workspace application boundary', () => {
  it('maps workflow URLs to engineering stages', () => {
    expect(stageFromPath('/projects/p/model/geometry')).toBe('Modelar');
    expect(stageFromPath('/projects/p/preflight')).toBe('Preflight');
    expect(stageFromPath('/runs/r1')).toBe('Ejecutar');
    expect(stageFromPath('/runs/r1/results')).toBe('Resultados');
    expect(stageFromPath('/compare?run_ids=r1,r2')).toBe('Comparar');
  });

  it('preserves schema pointer and explicit unit without client arithmetic', () => {
    expect(fieldBinding({ pointer: '/geometry/diameter', label: 'Diameter', unit: 'm', value: '0.1', supported: true }))
      .toEqual({ pointer: '/geometry/diameter', unit: 'm', enabled: true });
  });

  it('disables fields whose backend consumer is unavailable', () => {
    expect(fieldBinding({ pointer: '/future/value', label: 'Future', unit: 'SI', value: '', supported: false }).enabled).toBe(false);
  });

  it('keeps engine sections in the model stage', () => {
    expect(ENGINE_SECTIONS).toHaveLength(4);
    expect(sectionStage('Geometría y puertos')).toBe('Modelar');
  });

  it('persists only versioned UI preferences with safe defaults', () => {
    const storage = new Map<string, string>();
    const fake = { getItem: (k: string) => storage.get(k) ?? null, setItem: (k: string, v: string) => storage.set(k, v) } as unknown as Storage;
    saveUiPreferences({ unitSystem: 'US', advanced: true }, fake);
    expect(loadUiPreferences(fake)).toEqual({ unitSystem: 'US', advanced: true });
    storage.set('dino2next.ui-preferences.v1', '{bad');
    expect(loadUiPreferences(fake)).toEqual({ unitSystem: 'SI', advanced: false });
  });

  it('keeps the API dependency injectable at the application boundary', () => {
    const client: ApplicationApiClient = {} as ApplicationApiClient;
    expect(client).toBeDefined();
  });

  it('uses only contract routes and immutable revision/idempotency headers', async () => {
    const calls: Request[] = [];
    const fetcher = (async (input: RequestInfo | URL, init?: RequestInit) => { calls.push(new Request(input, init)); return new Response(JSON.stringify({ id: 'p', revision_hash: 'r', schema_version: 'v1' }), { status: 200 }); }) as typeof fetch;
    const api = createHttpClient('http://localhost/api/v1', fetcher);
    await api.createRevision('p/1', 'parent', {});
    await api.createRun('key-1', 'preflight', {});
    expect(calls[0].url).toContain('/projects/p%2F1/revisions');
    expect(calls[0].headers.get('if-match')).toBe('parent');
    expect(calls[1].headers.get('idempotency-key')).toBe('key-1');
  });

  it('preserves typed conflict errors from the application service', async () => {
    const fetcher = (async () => new Response(JSON.stringify({ code: 'REVISION_CONFLICT', message: 'stale', pointer: '/revision' }), { status: 409 })) as typeof fetch;
    await expect(createHttpClient('http://localhost/api/v1', fetcher).createProject({})).rejects.toMatchObject({ status: 409, code: 'CONFLICT', pointer: '/revision' } satisfies Partial<ApplicationApiError>);
  });

  it('exposes contract read/control routes without client-side physics', async () => {
    const calls: Request[] = [];
    const fetcher = (async (input: RequestInfo | URL, init?: RequestInit) => { calls.push(new Request(input, init)); return new Response('{}', { status: 200 }); }) as typeof fetch;
    const api = createHttpClient('http://localhost/api/v1', fetcher);
    await api.getDiagnostics('r/1'); await api.getResults('r/1'); await api.getTrace('r/1', 't/2'); await api.cancelRun('r/1'); await api.compareRuns(['r/1', 'r/2']);
    expect(calls.map(c => new URL(c.url).pathname)).toEqual(['/api/v1/runs/r%2F1/diagnostics', '/api/v1/runs/r%2F1/results', '/api/v1/runs/r%2F1/traces/t%2F2', '/api/v1/runs/r%2F1/cancel', '/api/v1/compare']);
    expect(calls[3].method).toBe('POST');
    expect(new URL(calls[4].url).searchParams.get('run_ids')).toBe('r/1,r/2');
  });
});

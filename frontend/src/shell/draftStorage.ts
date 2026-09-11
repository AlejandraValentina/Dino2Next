/** Local draft continuity only; drafts are never simulation evidence or revisions. */
const PREFIX = 'dino2next.ui-draft.v1:';
export function loadDraft(projectId: string, storage: Storage = globalThis.localStorage): Record<string, string> {
  try {
    const value: unknown = JSON.parse(storage.getItem(PREFIX + projectId) ?? '{}');
    if (!value || typeof value !== 'object') return {};
    return Object.fromEntries(Object.entries(value).filter(([, v]) => typeof v === 'string'));
  } catch { return {}; }
}
export function saveDraft(projectId: string, values: Record<string, string>, storage: Storage = globalThis.localStorage): void {
  storage.setItem(PREFIX + projectId, JSON.stringify(values));
}

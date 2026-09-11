export type UiPreferences = { unitSystem: 'SI' | 'US'; advanced: boolean };
const KEY = 'dino2next.ui-preferences.v1';
const DEFAULTS: UiPreferences = { unitSystem: 'SI', advanced: false };

export function loadUiPreferences(storage: Storage = globalThis.localStorage): UiPreferences {
  try {
    const parsed: unknown = JSON.parse(storage.getItem(KEY) ?? 'null');
    if (!parsed || typeof parsed !== 'object') return { ...DEFAULTS };
    const p = parsed as Record<string, unknown>;
    return { unitSystem: p.unitSystem === 'US' ? 'US' : 'SI', advanced: p.advanced === true };
  } catch { return { ...DEFAULTS }; }
}

export function saveUiPreferences(value: UiPreferences, storage: Storage = globalThis.localStorage): void {
  storage.setItem(KEY, JSON.stringify({ unitSystem: value.unitSystem, advanced: value.advanced }));
}

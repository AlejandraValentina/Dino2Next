import type { ModelField } from '../shell/AppShell';
export const modelRouteEntry = { path: '/projects/:id/model/:section', title: 'Modelar' } as const;
export function fieldBinding(field: ModelField) {
  return { pointer: field.pointer, unit: field.unit, enabled: field.supported };
}

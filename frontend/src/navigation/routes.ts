export type RouteEntry = { path: string; title: string; render: () => HTMLElement };

export const APP_STAGES = ['Modelar', 'Preflight', 'Ejecutar', 'Resultados', 'Comparar'] as const;
export type AppStage = (typeof APP_STAGES)[number];

export function stageFromPath(path: string): AppStage {
  if (path.includes('/preflight')) return 'Preflight';
  if (path.includes('/results')) return 'Resultados';
  if (path.includes('/runs/')) return 'Ejecutar';
  if (path.includes('/compare')) return 'Comparar';
  return 'Modelar';
}

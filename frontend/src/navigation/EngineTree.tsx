import type { AppStage } from './routes';

export const ENGINE_SECTIONS = ['Proyecto', 'Geometría y puertos', 'Escape', 'Punto de operación'] as const;
export type EngineSection = (typeof ENGINE_SECTIONS)[number];

export function EngineTree({ active, onSelect }: { active: EngineSection; onSelect: (section: EngineSection) => void }) {
  return <nav aria-label="Árbol del motor"><ul>{ENGINE_SECTIONS.map(section =>
    <li key={section}><button type="button" aria-current={active === section ? 'page' : undefined}
      onClick={() => onSelect(section)}>{section}</button></li>)}</ul></nav>;
}

export function sectionStage(_section: EngineSection): AppStage { return 'Modelar'; }

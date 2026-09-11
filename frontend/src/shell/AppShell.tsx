import { useState } from 'react';
import { APP_STAGES, type AppStage } from '../navigation/routes';
import { EngineTree, type EngineSection } from '../navigation/EngineTree';
import { loadUiPreferences, saveUiPreferences } from './preferences';

export type ModelField = { pointer: string; label: string; unit: string; value: string; supported: boolean };

export function AppShell({ fields = [] }: { fields?: ModelField[] }) {
  const [stage, setStage] = useState<AppStage>('Modelar');
  const [section, setSection] = useState<EngineSection>('Proyecto');
  const [preferences, setPreferences] = useState(() => loadUiPreferences());
  const updatePreferences = (advanced: boolean) => { const next = { ...preferences, advanced }; setPreferences(next); saveUiPreferences(next); };
  return <main aria-label="Dino2Next engineering application">
    <header><h1>Dino2Next</h1><p>Simulador de ingeniería</p></header>
    <nav aria-label="Flujo de trabajo"><ol>{APP_STAGES.map(item =>
      <li key={item}><button type="button" aria-current={stage === item ? 'step' : undefined} onClick={() => setStage(item)}>{item}</button></li>
    )}</ol></nav>
    <section aria-labelledby="stage-title"><h2 id="stage-title">{stage}</h2>
      {stage === 'Modelar' ? <><EngineTree active={section} onSelect={setSection} /><label><input type="checkbox" checked={preferences.advanced} onChange={e => updatePreferences(e.target.checked)} /> Opciones avanzadas</label><ModelPanel fields={fields} section={section} /></> : <PendingStage stage={stage} />}
    </section>
  </main>;
}

function PendingStage({ stage }: { stage: AppStage }) {
  if (stage === 'Modelar') return null;
  const labels: Record<Exclude<AppStage, 'Modelar'>, string> = {
    Preflight: 'La revisión se habilitará al recibir los diagnósticos del servicio.',
    Ejecutar: 'La ejecución requiere una revisión aceptada y un run creado por el servicio.',
    Resultados: 'Los resultados se mostrarán cuando el servicio publique su manifiesto.',
    Comparar: 'La comparación requiere referencias de resultados compatibles.',
  };
  return <p role="status">{labels[stage]}</p>;
}

function ModelPanel({ fields, section }: { fields: ModelField[]; section: EngineSection }) {
  return <div><p>Sección: {section}. Configure el modelo y guarde una revisión inmutable.</p>
    <fieldset><legend>Configuración básica</legend>{fields.length === 0
      ? <p role="status">No hay descriptores de campos disponibles.</p>
      : fields.map(field => <label key={field.pointer}>{field.label} ({field.unit})
        <input name={field.pointer} defaultValue={field.value} disabled={!field.supported} aria-disabled={!field.supported} />
      </label>)}</fieldset>
  </div>;
}

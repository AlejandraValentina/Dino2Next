import { useState } from 'react';
import { APP_STAGES, type AppStage } from '../navigation/routes';

export type ModelField = { pointer: string; label: string; unit: string; value: string; supported: boolean };

export function AppShell({ fields = [] }: { fields?: ModelField[] }) {
  const [stage, setStage] = useState<AppStage>('Modelar');
  return <main aria-label="Dino2Next engineering application">
    <header><h1>Dino2Next</h1><p>Simulador de ingeniería</p></header>
    <nav aria-label="Flujo de trabajo"><ol>{APP_STAGES.map(item =>
      <li key={item}><button type="button" aria-current={stage === item ? 'step' : undefined} onClick={() => setStage(item)}>{item}</button></li>
    )}</ol></nav>
    <section aria-labelledby="stage-title"><h2 id="stage-title">{stage}</h2>
      {stage === 'Modelar' ? <ModelPanel fields={fields} /> : <p>Esta etapa queda disponible al recibir la interfaz ApplicationAPI de S17.</p>}
    </section>
  </main>;
}

function ModelPanel({ fields }: { fields: ModelField[] }) {
  return <div><p>Configure el modelo y guarde una revisión inmutable.</p>
    <fieldset><legend>Configuración básica</legend>{fields.length === 0
      ? <p role="status">No hay descriptores de campos disponibles.</p>
      : fields.map(field => <label key={field.pointer}>{field.label} ({field.unit})
        <input name={field.pointer} defaultValue={field.value} disabled={!field.supported} aria-disabled={!field.supported} />
      </label>)}</fieldset>
  </div>;
}

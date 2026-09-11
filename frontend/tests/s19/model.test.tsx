import { describe, expect, it } from 'vitest';
import { stageFromPath } from '../../src/navigation/routes';
import { fieldBinding } from '../../src/route_entries/model';

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
});

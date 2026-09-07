"""Actual fixed-mesh temporal verification; no analytic spatial oracle."""
from hashlib import sha256
import importlib.util
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]


def load_driver():
    spec = importlib.util.spec_from_file_location('canonical_driver', ROOT/'validation/fixtures/VAL-006/canonical_execution.py')
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def test_temporal_reference_and_four_actual_step_sequences():
    driver = load_driver()
    fixture_path=ROOT/'validation/fixtures/VAL-027/input.json'
    assert sha256(fixture_path.read_bytes()).hexdigest() == '1e43d94e07b31965f5c2347c58282be3d3e4ff710693faa2aae241f6e904c5e4'
    fixture=json.loads(fixture_path.read_text())
    source=ROOT/fixture['frozen_source']
    assert sha256(source.read_bytes()).hexdigest()==fixture['frozen_source_sha256']
    assert fixture['frozen_fiche']==json.loads(source.read_text())['fixtures']['VAL-027']
    assert fixture['dt'] == [.002, .001, .0005, .00025]
    kernel, initial, reference = driver.setup('VAL-027', 40, fixture['cases'][0])
    rhs = driver.CanonicalRHS(kernel, 'VAL-027', fixture['cases'][0], reference)
    t, oracle, nfev = reference.integrate(kernel, initial, rhs)
    _, cross, cross_nfev = reference.integrate(kernel, initial, rhs, crosscheck=True)
    discrepancy = float(np.max(abs(oracle-cross)))
    out = ROOT/'artifacts/VAL-027'; out.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(out/'temporal-reference.npz', times=t, Q=oracle, cross=cross)
    report = dict(classification='NUMERICAL_VERIFICATION_TEMPORAL_ONLY', N=40,
                  reference_discrepancy=discrepancy, nfev=nfev, cross_nfev=cross_nfev,
                  qualification='REFERENCE_QUALIFIED' if discrepancy <= 1e-11 else 'REFERENCE_NOT_QUALIFIED',
                  hashes={str(p.relative_to(ROOT)):sha256(p.read_bytes()).hexdigest() for p in [
                      ROOT/'src/dino2next/numerics/__init__.py', ROOT/'validation/references/VAL-027/reference.py',
                      ROOT/'validation/fixtures/VAL-006/canonical_execution.py', ROOT/'validation/fixtures/VAL-006/gamma_adapter.py']}, levels=[])
    (out/'acceptance.json').write_text(json.dumps(report, indent=2)+'\n')
    assert discrepancy <= 1e-11, 'REFERENCE_NOT_QUALIFIED'
    for level, dt in enumerate(fixture['dt']):
        state = initial; states = [state.Q]; rows = []; diagnostics = []
        count = round(.1/dt)
        for i in range(count):
            attempt = kernel.propose_step(state, rhs, float(i*dt), dt)
            assert attempt.accepted, (attempt.rejection, attempt.diagnostics)
            stage_records = [d for d in attempt.diagnostics if d[0] == 'stage']
            assert len(stage_records) == 2
            assert all(d[3] == 1. and d[5] == 0 for d in stage_records), 'REFERENCE_NOT_QUALIFIED: candidate guard changed the compared RHS'
            state = attempt.state; states.append(state.Q)
            exact = oracle[(i+1)*(400//count)]
            err = state.Q-exact
            rows.append(dict(time=(i+1)*dt, density_L1=float(np.mean(abs(err[:,0]))),
                             state_L1=np.mean(abs(err),axis=0).tolist(),
                             state_L2=np.sqrt(np.mean(err**2,axis=0)).tolist(),
                             state_Linf=np.max(abs(err),axis=0).tolist()))
            diagnostics.append(attempt.diagnostics)
        np.savez_compressed(out/f'dt-{dt}.npz', times=np.arange(count+1)*dt, Q=states)
        report['levels'].append(dict(dt=dt, steps=count, rows=rows, diagnostics=diagnostics,
                                    max_density_L1=max(row['density_L1'] for row in rows),
                                    final_density_L1=rows[-1]['density_L1']))
        (out/'acceptance.json').write_text(json.dumps(report, indent=2)+'\n')
    errors = [row['max_density_L1'] for row in report['levels']]
    orders = np.log2(np.asarray(errors[:-1])/errors[1:])
    report['orders'] = orders.tolist()
    floor_qualified = min(errors[:3]) > discrepancy
    passed = floor_qualified and np.all(np.isfinite(orders)) and errors[-1] <= 1e-10 and np.all((orders[:2]>=1.8)&(orders[:2]<=2.2))
    report['result'] = 'PASS' if passed else ('REFERENCE_NOT_QUALIFIED' if not floor_qualified else 'FAIL')
    (out/'acceptance.json').write_text(json.dumps(report, indent=2)+'\n')
    assert errors[-1] <= 1e-10
    assert min(errors[:3]) > discrepancy, 'REFERENCE_NOT_QUALIFIED: temporal order at reference floor'
    assert np.all((orders[:2]>=1.8)&(orders[:2]<=2.2)), orders

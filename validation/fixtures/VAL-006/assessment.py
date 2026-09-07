"""Frozen S06 numerical metrics, run against independently qualified references."""
import importlib.util
import json
from hashlib import sha256
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]


def driver():
    spec = importlib.util.spec_from_file_location('canonical_execution', Path(__file__).with_name('canonical_execution.py'))
    result = importlib.util.module_from_spec(spec); spec.loader.exec_module(result)
    return result


def run_case(fixture_id, case_index):
    fixture_path = ROOT/f'validation/fixtures/{fixture_id}/input.json'
    # Pins executable coverage (all meshes/CFL/cases), not only descriptive fiche.
    approved_input_hashes = {'VAL-006': '97550cd33c23f09b911d35968041cdf2b660d218114991d563fb7f3da607df9f', 'VAL-007': 'd23e561eca59ce4b72931992f1782c106a5ca36c594c36909525474ab0d2fb6e', 'VAL-009': '862d6b5caa7b79495147649fcb3a57cc38e93afa820f3a3f5d5c1831429b65de', 'VAL-010': '71951a0ae0e6d3fa7c0508fb9200f258994417ca6cfc519511e6460b6f17d858', 'VAL-011': '88e4fa08d660ee667e60ceeb281b2f79c35055945658cd7f15b3b489b4334c7c'}
    assert sha256(fixture_path.read_bytes()).hexdigest() == approved_input_hashes[fixture_id]
    fixture = json.loads(fixture_path.read_text())
    source = ROOT/fixture['frozen_source']
    assert sha256(source.read_bytes()).hexdigest() == fixture['frozen_source_sha256']
    assert fixture['frozen_fiche'] == json.loads(source.read_text())['fixtures'][fixture_id]
    qualification = json.loads((ROOT/f'validation/references/{fixture_id}/qualification.json').read_text())
    assert qualification['status'] == 'REFERENCE_QUALIFIED'
    assert qualification['candidate_imports'] is False
    assert qualification['fixture_source_sha256'] == fixture['frozen_source_sha256']
    assert qualification['qualification_sha256'] == sha256((ROOT/'validation/references/VAL-006/qualify.py').read_bytes()).hexdigest()
    assert qualification['reference_sha256'] == sha256((ROOT/f'validation/references/{fixture_id}/reference.py').read_bytes()).hexdigest()
    expected_record = json.loads((ROOT/f'validation/expected/{fixture_id}/acceptance.json').read_text())
    assert expected_record['source_sha256'] == fixture['frozen_source_sha256']
    expected = expected_record['thresholds']
    normative_thresholds = {
        'VAL-006': dict(finest_density_L1_max=.004375,last_two_orders_min=.5,ledger_max=1e-10),
        'VAL-007': dict(pressure_velocity_Linf_max=1e-10,density_L1_cells_max=2,stationary_roundoff_multiplier=256),
        'VAL-009': dict(amplitude_N_factor=2,amplitude_epsilon_factor=10,phase_pi_over_N=1,smooth_order_min=1.8),
        'VAL-010': dict(finest_rigid_normalized_L1_max=.01,free_amplitude_relative_max=.01,free_phase_pi_over_N=1),
        'VAL-011': dict(rest_pressure_velocity_Linf_max=1e-10,finest_density_L1_max=2e-6,smooth_order_min=1.8,ledger_max=1e-10)}
    assert expected == normative_thresholds[fixture_id], 'Frozen threshold record changed'
    d = driver(); case = fixture['cases'][case_index]; results = []
    if fixture_id == 'VAL-010' and case['kind'] == 'free':
        # Frozen sample j=75: ct=.75, hence both Gaussian centers equal1.
        # The full pressure reference is identically zero, not a tiny floating
        # Fourier denominator. No final-only exception exists in the fiche.
        out=ROOT/'artifacts/VAL-010'; out.mkdir(parents=True,exist_ok=True)
        (out/f"{case['name']}-assessment.json").write_text(json.dumps(dict(
            result='SCIENTIFIC_CHANGE_REQUIRED', sample_index=75, sample_count=101,
            time=.75/np.sqrt(1.4), exact_reference_coefficient=0,
            reason='VAL-010 maximum-timewise Fourier normalization requires nonzero Cref; incident and reflected pressure cancel at required sample75',
            case=case, evidence='artifacts/S06/canonical-setup-audit.json'),indent=2)+'\n')
        raise AssertionError('SCIENTIFIC_CHANGE_REQUIRED: VAL-010 free Cref=0 at mandatory sample75')
    for n in fixture['meshes']:
        for cfl in fixture['CFL']:
            record, state, reference = d.execute(fixture_id, n, case, cfl)
            rows = record['metrics']
            values = np.asarray([row['L1'] for row in rows])
            row = dict(N=n, CFL=cfl, max_L1=values.max(axis=0).tolist(),
                       final_L1=values[-1].tolist(), max_Linf=np.max([x['Linf'] for x in rows], axis=0).tolist(),
                       ledger_max=float(np.max(np.abs([x['ledger'] for x in rows]))),
                       steps=len(record['steps']), rejected=len(record['rejections']))
            if fixture_id in ('VAL-009', 'VAL-010') and case.get('kind') != 'rigid':
                k, _, _ = d.setup(fixture_id, n, case)
                raw = np.load(ROOT/f"artifacts/{fixture_id}/{case['name']}-N{n}-CFL{cfl}.npz")
                modes = []
                for time, q in zip(raw['times'], raw['Q']):
                    p = k.recover(q).V[:, 2]
                    C = reference.fourier_coefficient(state.mesh.cell_bounds, p-1)
                    Cref = reference.exact_fourier(float(time), epsilon=case['epsilon'])
                    assert abs(Cref) > 0, 'REFERENCE_NOT_QUALIFIED: zero Fourier reference'
                    modes.append(dict(time=float(time), C=[C.real,C.imag], Cref=[Cref.real,Cref.imag],
                        amplitude_relative_error=abs(abs(C)/abs(Cref)-1), phase_error=abs(np.angle(C/Cref))))
                row.update(modes=modes, amplitude_relative_error=max(m['amplitude_relative_error'] for m in modes),
                           phase_error=max(m['phase_error'] for m in modes))
            results.append(row)
    spatial = [x for x in results if x['CFL'] == .05]
    errors = np.asarray([x['max_L1'][0] for x in spatial])
    orders = np.log2(errors[:-1]/errors[1:]) if np.all(errors>0) else np.full(len(errors)-1, np.nan)
    report = dict(fixture=fixture_id, case=case, classification='NUMERICAL_VERIFICATION',
                  results=results, spatial_density_orders=orders.tolist(), result='METRICS_RECORDED_PENDING_ASSERTIONS')
    finest = fixture['meshes'][-1]
    temporal_fields = [np.load(ROOT/f"artifacts/{fixture_id}/{case['name']}-N{finest}-CFL{cfl}.npz")['Q'] for cfl in fixture['CFL']]
    report['finest_mesh_temporal_separation'] = [dict(CFL_pair=[a,b],
        max_state_difference=float(np.max(abs(qa-qb))),
        max_density_L1_difference=float(np.max(np.mean(abs(qa[:,:,0]-qb[:,:,0]),axis=1))))
        for a,b,qa,qb in zip(fixture['CFL'][:-1],fixture['CFL'][1:],temporal_fields[:-1],temporal_fields[1:])]
    if case.get('epsilon') == 5e-6:
        full_case = next(c for c in fixture['cases'] if c.get('epsilon') == 1e-5 and c.get('kind') == case.get('kind'))
        paired=[]
        for n in fixture['meshes']:
            full_path = ROOT/f"artifacts/{fixture_id}/{full_case['name']}-N{n}-CFL0.05.npz"
            assert full_path.exists(), 'Paired epsilon run is required'
            half_path=ROOT/f"artifacts/{fixture_id}/{case['name']}-N{n}-CFL0.05.npz"
            full=np.load(full_path); half=np.load(half_path)
            assert np.array_equal(full['times'],half['times']), 'Paired sample times differ'
            for raw_path in (full_path,half_path):
                identity=json.loads(raw_path.with_suffix('.json').read_text())
                assert identity['raw_sha256'] == sha256(raw_path.read_bytes()).hexdigest()
                assert identity['source_sha256'] == sha256(Path(__file__).with_name('canonical_execution.py').read_bytes()).hexdigest()
                assert all(sha256((ROOT/path).read_bytes()).hexdigest()==value for path,value in identity['hashes'].items()), 'Stale paired execution artifact'
            k,_,_=d.setup(fixture_id,n,case)
            differences=[]
            for qf,qh in zip(full['Q'],half['Q']):
                vf=k.recover(qf).V[:,:3]; vh=k.recover(qh).V[:,:3]
                perturbation_difference=(vf-np.array([1.,0.,1.]))/1e-5-(vh-np.array([1.,0.,1.]))/5e-6
                differences.append(np.mean(abs(perturbation_difference),axis=0))
            paired.append(dict(N=n,max_normalized_remainder=np.max(differences,axis=0).tolist(),
                full_raw_sha256=sha256(full_path.read_bytes()).hexdigest()))
        report['epsilon_halving_comparison']=paired
    path = ROOT/f"artifacts/{fixture_id}/{case['name']}-assessment.json"
    path.write_text(json.dumps(report, indent=2)+'\n')
    try:
        if fixture_id == 'VAL-006':
            assert errors[-1] <= expected['finest_density_L1_max'], errors
            assert np.all(np.diff(errors)<0), errors
            assert np.all(orders[-2:]>=expected['last_two_orders_min']), orders
            assert max(x['ledger_max'] for x in results) <= expected['ledger_max']
        elif fixture_id == 'VAL-007':
            assert max(max(x['max_Linf'][1:]) for x in results) <= expected['pressure_velocity_Linf_max']
            assert all(x['max_L1'][0] <= expected['density_L1_cells_max']/x['N'] for x in results)
            if case['speed'] == 0:
                assert max(x['max_Linf'][0] for x in results) <= 256*np.finfo(float).eps*2
            else:
                assert np.all(np.diff(errors)<0), errors
        elif fixture_id == 'VAL-009':
            assert all(x['amplitude_relative_error'] <= 2*(2*np.pi/x['N'])**2+10*case['epsilon'] for x in results)
            assert all(x['phase_error'] <= np.pi/x['N'] for x in results)
            # Preserve measured nonlinear remainder and orders; no subtraction.
            assert np.all(orders[-2:]>=expected['smooth_order_min']), orders
        elif fixture_id == 'VAL-010':
            if case['kind'] == 'rigid':
                assert spatial[-1]['max_L1'][2]/case['epsilon'] <= expected['finest_rigid_normalized_L1_max']
            else:
                assert all(x['amplitude_relative_error'] <= expected['free_amplitude_relative_max'] for x in results)
                assert all(x['phase_error'] <= np.pi/x['N'] for x in results)
        elif fixture_id == 'VAL-011':
            if not case['smooth']:
                assert max(max(x['max_Linf'][1:]) for x in results) <= expected['rest_pressure_velocity_Linf_max']
            else:
                assert errors[-1] <= expected['finest_density_L1_max'], errors
                assert np.all(orders[-2:]>=expected['smooth_order_min']), orders
            assert max(x['ledger_max'] for x in results) <= expected['ledger_max']
    except AssertionError as exc:
        report['result'] = 'VERIFICATION_FAILURE'; report['failure'] = str(exc)
        path.write_text(json.dumps(report, indent=2)+'\n')
        raise
    report['result'] = 'PASS'
    path.write_text(json.dumps(report, indent=2)+'\n')

"""SV-008 guarded NASA fixture; all error measurements retain the original window."""
from pathlib import Path
from hashlib import sha256
import importlib.util
import json
import math
import platform
import subprocess
import sys
import time as clock
from collections import deque

import numpy as np

from dino2next.gasdynamics import Mesh1D
from dino2next.numerics import NumericalKernel, StageRHS
from dino2next.thermo import (ThermoModel, ThermoDataset, DERIVED_SHA256,
                             RAW_SHA256, TRANSPORT_SHA256, GENERATOR_SHA256)

ROOT = Path(__file__).resolve().parents[3]
INPUT_SHA = 'd64f03d8a6bc81c2f793a7d9737031efcef810ddbaa3c33d6f1ea0a505b03810'
R4_FIXTURE_CATALOG_SHA256 = 'fd96f3e520828e12bc8483de9a437d5c3bba85bcf9269ef3675db8a6e265b513'
R4_CATALOGUE_SHA256 = '3b23f7a74995feef37f5d5535eea11dc04b269363f42642aa91ece8f733e15b7'


def frozen_source(fixture):
    current = ROOT/fixture['frozen_source']; expected = fixture['frozen_source_sha256']
    if sha256(current.read_bytes()).hexdigest() == expected:
        return current
    assert expected == R4_FIXTURE_CATALOG_SHA256
    archived = ROOT/'docs/science/C1.0/history/C1.0-R4'/current.name
    assert sha256(archived.read_bytes()).hexdigest() == expected
    return archived


def load_reference():
    path = ROOT/'validation/references/VAL-008/reference.py'
    spec = importlib.util.spec_from_file_location('nasa008_reference', path)
    result = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = result
    spec.loader.exec_module(result)
    return result


def regional_driver():
    """Load the material candidate without giving it access to this oracle."""
    path = ROOT/'validation/fixtures/VAL-008/regional_execution.py'
    spec = importlib.util.spec_from_file_location('nasa008_regional_candidate', path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def compensated(rows):
    return np.array([math.fsum(column) for column in np.asarray(rows).T])


def guarded_mesh(n, speed, end):
    m = math.ceil(n*speed*end)+4
    edges = np.arange(-m, n+m+1, dtype=float)/n
    assert edges[m] == 0 and edges[m+n] == 1 and edges[m+n//2] == .5
    assert m/n-speed*end >= 4/n-8*np.finfo(float).eps
    count = n+2*m
    return Mesh1D(tuple(map(float,edges)), (1.,)*count, (1.,)*(count+1), (1.,)*count), m


def kernel():
    data = ROOT/'docs/science/C1.0/datasets'
    return NumericalKernel(ThermoModel(ThermoDataset.from_files(
        data/'thermo_runtime_continuous_v1.json', data/'thermo_species.json',
        data/'thermo_transport.yaml', ROOT/'research/bcr_s03_nasa_inversion/generate.py',
        expected_sha256=DERIVED_SHA256, expected_raw_sha256=RAW_SHA256,
        expected_transport_sha256=TRANSPORT_SHA256, expected_generator_sha256=GENERATOR_SHA256)))


class GuardedRHS:
    def __init__(self, k, initial, speed):
        self.k, self.speed = k, speed
        self.left = np.repeat(initial.Q[:1], 4, axis=0)
        self.right = np.repeat(initial.Q[-1:], 4, axis=0)
        self.boundary = k.physical_flux(np.stack((initial.Q[0], initial.Q[-1])))
        self.stage_speeds = []

    def monitor(self, state, time, stage):
        return self.monitor_array(state.Q,time,stage)

    def monitor_array(self, q, time, stage):
        p = self.k.recover(q)
        measured = float(np.max(abs(p.V[:, 1])+p.a))
        self.stage_speeds.append(dict(time=time, stage=stage, max_speed=measured,
            minimum_density=float(np.min(p.V[:,0])),minimum_pressure=float(np.min(p.V[:,2])),
            minimum_temperature=float(np.min(p.T)),maximum_temperature=float(np.max(p.T)),
            minimum_species=np.min(q[:,3:8],axis=0).tolist(),minimum_origins=np.min(q[:,8:],axis=0).tolist()))
        assert measured <= self.speed, ('SETUP_CAUSAL_BOUND_FAILED', measured, self.speed)
        return p

    def __call__(self, state, time):
        self.monitor(state, time, 'RHS_PHYSICAL_STAGE')
        faces = self.k.reconstruct(state, boundary='physical', ghosts=(self.left, self.right))
        flux = self.k.interior_flux(faces, boundary_flux=self.boundary)
        active = np.flatnonzero((faces.contraction < 1)|(faces.flattening < 1)|faces.near)
        diagnostics = (('face_limiters', tuple((int(i), float(faces.contraction[i]),
                        float(faces.flattening[i]), bool(faces.near[i])) for i in active)),)
        return StageRHS(flux, np.zeros_like(state.Q), diagnostics)


def verify_fixture():
    path = ROOT/'validation/fixtures/VAL-008/input.json'
    assert sha256(path.read_bytes()).hexdigest() == INPUT_SHA
    fixture = json.loads(path.read_text())
    source = frozen_source(fixture)
    assert sha256(source.read_bytes()).hexdigest() == fixture['frozen_source_sha256']
    assert fixture['frozen_fiche'] == json.loads(source.read_text())['fixtures']['VAL-008']
    expected = json.loads((ROOT/'validation/expected/VAL-008/acceptance.json').read_text())
    assert expected['source_sha256'] == fixture['frozen_source_sha256']
    assert expected['thresholds'] == dict(operational_pressure_L1_max=5e-4,
        operational_pressure_Linf_max=5e-3,thermal_pressure_L1_max=2e-3,
        thermal_pressure_Linf_max=2e-2,shock_last_two_orders_min=.5,ledger_max=1e-10)
    return fixture


def execute(case, n, cfl, *, output_root=None):
    if case['kind'] == 'contact':
        return execute_regional_contact(case, n, cfl, output_root=output_root)
    fixture = verify_fixture()
    historical_catalogue = frozen_source(fixture)
    out = Path(output_root) if output_root else ROOT/'artifacts/VAL-008'
    out.mkdir(parents=True,exist_ok=True)
    artifact_stem = f"{case['name']}-N{n}-CFL{cfl}"
    reference = load_reference()
    qualification = json.loads((ROOT/'validation/references/VAL-008/qualification.json').read_text())
    assert qualification['status'] == 'REFERENCE_QUALIFIED'
    assert qualification['candidate_imports'] is False
    assert qualification['reference_sha256'] == sha256((ROOT/'validation/references/VAL-008/reference.py').read_bytes()).hexdigest()
    assert qualification['source_hashes'], 'REFERENCE_NOT_QUALIFIED: missing source bindings'
    required = {'validation/references/VAL-008/reference.py',
                'validation/references/VAL-008/qualify.py',
                'docs/science/C1.0/EXECUTABLE_VALIDATION_FIXTURES.json',
                'docs/science/C1.0/datasets/thermo_species.json',
                'docs/science/C1.0/datasets/thermo_runtime_continuous_v1.json'}
    assert required <= set(qualification['source_hashes']), 'REFERENCE_NOT_QUALIFIED: incomplete bindings'
    for source_path,digest in qualification['source_hashes'].items():
        candidate = ROOT/source_path
        if sha256(candidate.read_bytes()).hexdigest() != digest:
            assert source_path in ('docs/science/C1.0/EXECUTABLE_VALIDATION_FIXTURES.json',
                                   'docs/science/C1.0/EXECUTABLE_VALIDATION_CATALOGUE.md')
            assert digest in (R4_FIXTURE_CATALOG_SHA256, R4_CATALOGUE_SHA256)
            candidate = (historical_catalogue if digest == R4_FIXTURE_CATALOG_SHA256 else
                         ROOT/'docs/science/C1.0/history/C1.0-R4'/candidate.name)
        assert sha256(candidate.read_bytes()).hexdigest() == digest, ('REFERENCE_NOT_QUALIFIED',source_path)
    qualified_cases = [r for r in qualification['cases'] if r['parameters']==case['parameters']]
    assert len(qualified_cases)==1 and qualified_cases[0]['status']=='PASS'
    k = kernel(); solution = reference.solve(reference.Case(**case['parameters']))
    speed = fixture['guard_speeds'][case['kind']]
    mesh, m = guarded_mesh(n, speed, case['time']); window = slice(m,m+n)
    initial = solution.cell_averages(mesh.cell_bounds, 0.)
    state = k.state(mesh, initial['conserved']); rhs = GuardedRHS(k,state,speed)
    dx = np.asarray(mesh.dx); initial_primitive = k.recover(state.Q)
    rho_scale = float(np.max(initial_primitive.V[:,0])); u_scale = float(np.max(initial_primitive.a))
    scales = np.array([rho_scale, u_scale, 1e5])
    initial_window_mass = math.fsum(state.Q[window,0]*dx[window])
    ledgers = {}
    for ledger_name, selected, left, right in [('full',slice(None),0,len(dx)),('window',window,m,m+n)]:
        q0 = compensated(state.Q[selected]*dx[selected,None])
        reference_scale = np.full(12,q0[0]); reference_scale[1] *= u_scale
        reference_scale[2] = math.fsum(state.Q[selected,0]*initial_primitive.cv[selected]*initial_primitive.T[selected]*dx[selected])
        ledgers[ledger_name] = dict(selected=selected,left=left,right=right,initial=q0,
                             scale=reference_scale,terms=[],throughput=[])
    samples, refs, times, metrics, steps, retries = [state.Q], [initial['conserved'][window]], [0.], [], [], []
    primitive_refs = [np.column_stack([initial[key][window] for key in ('rho','u','p','T')])]
    start = clock.monotonic(); time = 0.
    source_digest = sha256(Path(__file__).read_bytes()).hexdigest()

    def checkpoint():
        assert sha256(Path(__file__).read_bytes()).hexdigest()==source_digest, 'SOURCE_CHANGED_DURING_RUN'
        partial = out/(artifact_stem+'-partial.npz')
        np.savez_compressed(partial,times=times,Q=samples,reference_window=refs,
            reference_primitive_rho_u_p_T=primitive_refs,cell_bounds=mesh.cell_bounds,window_indices=[m,m+n])
        partial.with_suffix('.json').write_text(json.dumps(dict(result='INCOMPLETE_NOT_ACCEPTANCE',
            case=case,N=n,CFL=cfl,samples=len(times),last_time=times[-1],accepted_steps=len(steps),
            rejected_steps=len(retries),metrics=metrics,source_sha256=source_digest,
            raw_sha256=sha256(partial.read_bytes()).hexdigest()),indent=2)+'\n',encoding='utf-8')

    def measure(time):
        recovered = rhs.monitor(state,time,'ACCEPTED_ENDPOINT')
        truth = solution.cell_averages(mesh.cell_bounds[m:m+n+1],time)
        actual = recovered.V[window,:3]
        exact = np.column_stack([truth[key] for key in ('rho','u','p')])
        error = abs(actual-exact)/scales
        row = dict(time=time,L1=np.sum(dx[window,None]*error,axis=0).tolist(),
                   L2=np.sqrt(np.sum(dx[window,None]*error**2,axis=0)).tolist(),Linf=error.max(axis=0).tolist(),
                   temperature_L1=float(np.sum(dx[window]*abs(recovered.T[window]-truth['T']))),
                   species_mass_L1=(np.sum(dx[window,None]*abs(state.Q[window,3:8]-truth['conserved'][:,3:8]),axis=0)/initial_window_mass).tolist(),ledgers={})
        for ledger_name, ledger in ledgers.items():
            current = compensated(state.Q[ledger['selected']]*dx[ledger['selected'],None])
            external = compensated(ledger['terms']) if ledger['terms'] else np.zeros(12)
            throughput = compensated(ledger['throughput']) if ledger['throughput'] else np.zeros(12)
            residual = compensated(np.stack([current,-ledger['initial'],-external]))
            row['ledgers'][ledger_name] = dict(inventory=current.tolist(),external=external.tolist(),
                normalized=(residual/(abs(ledger['initial'])+throughput+ledger['scale'])).tolist())
        metrics.append(row)
        temperature_error = abs(recovered.T[window]-truth['T'])
        species_error = abs(state.Q[window,3:8]-truth['conserved'][:,3:8])/initial_window_mass
        row.update(temperature_L2=float(np.sqrt(np.sum(dx[window]*temperature_error**2))),
                   temperature_Linf=float(np.max(temperature_error)),
                   species_mass_L2=np.sqrt(np.sum(dx[window,None]*species_error**2,axis=0)).tolist(),
                   species_mass_Linf=np.max(species_error,axis=0).tolist())
        return truth

    measure(0.)
    checkpoint()
    for target in np.linspace(0,case['time'],101)[1:]:
        while time < target:
            primitive = k.recover(state.Q)
            dt = min(float(cfl*np.min(dx/(abs(primitive.V[:,1])+primitive.a))),float(target-time))
            for retry in range(17):
                mapped_tail = deque(maxlen=3)
                def identity_mapper(q,stage_time):
                    mapped_tail.append((q,stage_time))
                    return q
                attempt = k.propose_step(state,rhs,float(time),float(dt),
                    trial_state_mapper=identity_mapper,initial_Z=state.Q)
                if attempt.accepted: break
                retries.append(dict(time=time,dt=dt,rejection=attempt.rejection,diagnostics=attempt.diagnostics))
                assert attempt.rejection in ('LOW_ORDER_STAGE_INADMISSIBLE_RETRY_DT','FLUX_LIMIT_ROUND_OFF_RETRY_DT'), retries[-1]
                dt /= 2
                assert time+dt > time
            else: raise AssertionError('RETRY_LIMIT_REACHED')
            # The selected second Euler endpoint and its two final mappings are
            # the last three identity calls. Failed high trials are not stages.
            assert len(mapped_tail)==3
            assert all(np.array_equal(q,attempt.state.Q) for q,_ in list(mapped_tail)[1:])
            rhs.monitor_array(mapped_tail[0][0],mapped_tail[0][1],'ACCEPTED_SECOND_EULER_ENDPOINT')
            state = attempt.state; time = float(target) if dt == target-time else time+dt
            rhs.monitor(state,time,'ACCEPTED_STEP')
            steps.append(dict(time=time,dt=dt,diagnostics=attempt.diagnostics))
            for ledger in ledgers.values():
                a,b = attempt.face_integrals[ledger['left']],attempt.face_integrals[ledger['right']]
                ledger['terms'].append(a-b); ledger['throughput'].append(abs(a)+abs(b))
        truth = measure(time)
        samples.append(state.Q); refs.append(truth['conserved']); times.append(time)
        primitive_refs.append(np.column_stack([truth[key] for key in ('rho','u','p','T')]))
        checkpoint()
    path = out/(artifact_stem+'.npz')
    np.savez_compressed(path,times=times,Q=samples,reference_window=refs,
                        reference_primitive_rho_u_p_T=primitive_refs,
                        cell_bounds=mesh.cell_bounds,window_indices=[m,m+n])
    record = dict(classification='NUMERICAL_VERIFICATION',result='EXECUTED_PENDING_ASSESSMENT',case=case,N=n,CFL=cfl,
        guard_cells_each_side=m,speed_bound=speed,metrics=metrics,steps=steps,rejections=retries,
        physical_stage_speeds=rhs.stage_speeds,elapsed_seconds=clock.monotonic()-start,
        reference_qualification=qualified_cases[0],
        raw_sha256=sha256(path.read_bytes()).hexdigest(),commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        environment=dict(python=platform.python_version(),numpy=np.__version__),
        hashes={str(p.relative_to(ROOT)):sha256(p.read_bytes()).hexdigest() for p in [Path(__file__),
            ROOT/'src/dino2next/numerics/__init__.py', ROOT/'validation/references/VAL-008/reference.py',
            ROOT/'validation/references/VAL-008/qualification.json',ROOT/'validation/fixtures/VAL-008/input.json']})
    path.with_suffix('.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
    return record


def execute_regional_contact(case, n, cfl, *, output_root=None, checkpoint_path=None, resume=False,
                             stop_after_steps=None):
    """Assess a W/I12 contact candidate against the frozen external oracle.

    Candidate construction and time stepping live in regional_execution.py;
    this adapter is the only place where the independently qualified reference
    is loaded and compared.
    """
    fixture = verify_fixture()
    if case['kind'] != 'contact':
        raise ValueError('Regional contact assessment requires a contact case')
    out = Path(output_root) if output_root else ROOT/'artifacts/VAL-008'
    out.mkdir(parents=True, exist_ok=True)
    stem = f"{case['name']}-N{n}-CFL{cfl}"
    reference = load_reference(); solution = reference.solve(reference.Case(**case['parameters']))
    qualification = json.loads((ROOT/'validation/references/VAL-008/qualification.json').read_text())
    assert qualification['status'] == 'REFERENCE_QUALIFIED' and qualification['candidate_imports'] is False
    qualified = [row for row in qualification['cases'] if row['parameters'] == case['parameters']]
    assert len(qualified) == 1 and qualified[0]['status'] == 'PASS'
    candidate = regional_driver()
    guard = math.ceil(n*fixture['guard_speeds']['contact']*case['time'])+4
    run = candidate.run_contact(case, n, cfl, guard_cells=guard, samples=fixture['sampling_points'],
                                checkpoint_path=checkpoint_path, resume=resume,
                                stop_after_steps=stop_after_steps)
    if run.get('incomplete'):
        partial = dict(classification='NUMERICAL_VERIFICATION', result='INCOMPLETE_RESTART_AVAILABLE',
            acceptance='NO_PASS', case=case, N=n, CFL=cfl, guard_cells_each_side=guard,
            checkpoint_path=str(checkpoint_path), regional_candidate=run['classification'],
            regional_kernel_identity=run['kernel_identity'], source_sha256=run['source_sha256'],
            step_audit_path=run['step_audit_path'])
        (out/(stem+'-partial.json')).write_text(json.dumps(partial, indent=2)+'\n', encoding='utf-8')
        return partial
    edges = np.linspace(0., 1., n+1); dx = np.diff(edges)
    initial_truth = solution.cell_averages(edges, 0.)
    initial_rho = float(np.max(initial_truth['rho']))
    initial_a = float(max(item.a for item in run['states'][0].regional_states.states))
    scales = np.array((initial_rho, initial_a, 1e5))
    reference_initial = np.sum(initial_truth['conserved']*dx[:, None], axis=0)
    metrics = []; Q = []; reference_window = []; primitive_reference = []

    def ledger_row(snapshot):
        result = {}
        for name, value in snapshot.items():
            initial = np.asarray(value['initial']); external = np.asarray(value['external']); sources = np.asarray(value['sources'])
            current = np.asarray(value['inventory'])
            throughput = np.asarray(value['throughput'])
            # Each conserved component has its own non-zero reference scale;
            # mass is never reused as momentum/energy scale.
            physical_reference = reference_initial if name == 'window' else initial
            mass_scale = max(abs(initial[0]), abs(physical_reference[0]), np.finfo(float).tiny)
            # ST-003 uses declared physical scales per conserved component:
            # momentum m*a, energy m*a^2, species/origins m when their initial
            # signed inventory is exactly zero.
            reference_scale = np.array((mass_scale, mass_scale*initial_a,
                max(abs(initial[2]), abs(physical_reference[2]), mass_scale*initial_a*initial_a),
                *[max(abs(initial[index]), abs(physical_reference[index]), mass_scale) for index in range(3, 12)]))
            result[name] = dict(inventory=current.tolist(), external=external.tolist(), sources=sources.tolist(),
                normalized=((current-initial-external-sources)/(abs(initial)+throughput+reference_scale)).tolist())
        return result

    for time, state, snapshot in zip(run['times'], run['states'], run['ledger_samples']):
        observed = candidate.pressure_observation(state, edges)
        truth = solution.cell_averages(edges, float(time))
        actual = np.column_stack((observed['conservative'][:, 0], observed['velocity'], observed['pressure']))
        exact = np.column_stack([truth[key] for key in ('rho', 'u', 'p')])
        error = abs(actual-exact)/scales
        species_error = abs(observed['conservative'][:, 3:8]-truth['conserved'][:, 3:8]) / float(np.sum(initial_truth['conserved'][:,0]*dx))
        temperature_error = abs(observed['temperature']-truth['T'])
        metrics.append(dict(time=float(time), L1=np.sum(dx[:,None]*error,axis=0).tolist(),
            L2=np.sqrt(np.sum(dx[:,None]*error**2,axis=0)).tolist(), Linf=np.max(error,axis=0).tolist(),
            temperature_L1=float(np.sum(dx*temperature_error)), temperature_L2=float(np.sqrt(np.sum(dx*temperature_error**2))),
            temperature_Linf=float(np.max(temperature_error)), species_mass_L1=np.sum(dx[:,None]*species_error,axis=0).tolist(),
            species_mass_L2=np.sqrt(np.sum(dx[:,None]*species_error**2)).tolist(), species_mass_Linf=np.max(species_error,axis=0).tolist(),
            ledgers=ledger_row(snapshot)))
        Q.append(observed['conservative']); reference_window.append(truth['conserved'])
        primitive_reference.append(np.column_stack([truth[key] for key in ('rho','u','p','T')]))
    path = out/(stem+'.npz')
    np.savez_compressed(path, times=run['times'], Q=Q, reference_window=reference_window,
        reference_primitive_rho_u_p_T=primitive_reference, cell_bounds=edges, window_indices=[0,n])
    sources = (Path(__file__), ROOT/'validation/fixtures/VAL-008/regional_execution.py',
               ROOT/'src/dino2next/gasdynamics/regional.py', ROOT/'src/dino2next/numerics/regional.py')
    record = dict(classification='NUMERICAL_VERIFICATION', result='EXECUTED_PENDING_ASSESSMENT', case=case, N=n, CFL=cfl,
        guard_cells_each_side=guard, metrics=metrics, regional_candidate=run['classification'],
        regional_kernel_identity=run['kernel_identity'], reference_qualification=qualified[0], raw_sha256=sha256(path.read_bytes()).hexdigest(),
        regional_rejected_trials=len(run['trials']), regional_rejected_trial_audit_path=run['trial_audit_path'],
        regional_rejected_trial_audit_sha256=(sha256(Path(run['trial_audit_path']).read_bytes()).hexdigest()
                                              if run['trial_audit_path'] else None), regional_guard_audit=run['guard_audit'],
        regional_causal_audit=run['causal_audit'], regional_step_audit=run['step_audit'], regional_ledger_samples=[
            {name:{key:np.asarray(value[key]).tolist() for key in ('initial','inventory','external','sources','throughput')}
             for name,value in sample.items()} for sample in run['ledger_samples']],
        regional_step_audit_path=run['step_audit_path'], regional_step_audit_sha256=(
            sha256(Path(run['step_audit_path']).read_bytes()).hexdigest() if run['step_audit_path'] else None),
        commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        environment=dict(python=platform.python_version(),numpy=np.__version__),
        hashes={str(source.relative_to(ROOT)):sha256(source.read_bytes()).hexdigest() for source in sources})
    path.with_suffix('.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
    return record

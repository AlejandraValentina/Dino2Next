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


def load_reference():
    path = ROOT/'validation/references/VAL-008/reference.py'
    spec = importlib.util.spec_from_file_location('nasa008_reference', path)
    result = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = result
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
    source = ROOT/fixture['frozen_source']
    assert sha256(source.read_bytes()).hexdigest() == fixture['frozen_source_sha256']
    assert fixture['frozen_fiche'] == json.loads(source.read_text())['fixtures']['VAL-008']
    expected = json.loads((ROOT/'validation/expected/VAL-008/acceptance.json').read_text())
    assert expected['source_sha256'] == fixture['frozen_source_sha256']
    assert expected['thresholds'] == dict(operational_pressure_L1_max=5e-4,
        operational_pressure_Linf_max=5e-3,thermal_pressure_L1_max=2e-3,
        thermal_pressure_Linf_max=2e-2,shock_last_two_orders_min=.5,ledger_max=1e-10)
    return fixture


def execute(case, n, cfl, *, output_root=None):
    fixture = verify_fixture()
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
        assert sha256((ROOT/source_path).read_bytes()).hexdigest() == digest, ('REFERENCE_NOT_QUALIFIED',source_path)
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

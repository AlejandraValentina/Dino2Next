"""MR-008 contact runner using declared physical regions, never EOS(Qbar)."""
from hashlib import sha256
from pathlib import Path
import json
import os
from time import perf_counter

import numpy as np

from dino2next.gasdynamics import CumulativeVolumeGeometry, Mesh1D, PolynomialSegment, RegionalDuctState
from dino2next.numerics.regional import RegionalNumericalKernel
from dino2next.thermo import ThermoDataset, ThermoModel

ROOT = Path(__file__).resolve().parents[3]


def _thermo():
    data = ROOT/'docs/science/C1.0/datasets'
    paths = (data/'thermo_runtime_continuous_v1.json', data/'thermo_species.json',
             data/'thermo_transport.yaml', ROOT/'research/bcr_s03_nasa_inversion/generate.py')
    digest = lambda path: sha256(path.read_bytes()).hexdigest()
    return ThermoModel(ThermoDataset.from_files(*paths, expected_sha256=digest(paths[0]),
        expected_raw_sha256=digest(paths[1]), expected_transport_sha256=digest(paths[2]),
        expected_generator_sha256=digest(paths[3])))


def _composition(pair):
    if pair == 0:
        return ((0., 0., 1., 0., 0.), (0., 0., 0., 1., 0.)), (600., 600.)
    if pair == 1:
        return ((0., 0., 1., 0., 0.), (0., 0., 0., 1., 0.)), (600., 1800.)
    if pair != 2:
        raise ValueError('Unknown frozen VAL-008 pair')
    # Frozen phi=.7 reactant/product mole counts; R_i is inversely proportional
    # to molecular weight, so it converts the declared mole vector to mass.
    phi = .7
    left = np.array((1., 12.5/phi, 47./phi, 0., 0.))
    right = np.array((0., 12.5/phi-12.5, 47./phi, 8., 9.))
    inverse_R = 1/np.asarray(_thermo().species_properties(300.).R)
    return (tuple(left*inverse_R/np.sum(left*inverse_R)),
            tuple(right*inverse_R/np.sum(right*inverse_R))), (400., 1800.)


def initial_state(case, n, guard_cells):
    """Build the declared two-material contact from fixture parameters only."""
    if case['kind'] != 'contact' or case['parameters']['pressure_ratio'] is not None:
        raise ValueError('MR-008 regional route requires an explicitly declared contact')
    m = int(guard_cells)
    edges = tuple(map(float, np.arange(-m, n+m+1)/n))
    assert .5 in edges
    geometry = CumulativeVolumeGeometry(PolynomialSegment(edges[0], edges[-1], (1.,), (1.,)))
    mesh = Mesh1D(edges, (1.,)*(len(edges)-1), (1.,)*len(edges), (1.,)*(len(edges)-1))
    (left_y, right_y), (left_t, right_t) = _composition(case['parameters']['pair'])
    u = float(case['parameters']['velocity'])
    physical = tuple((left_t, 1e5, u, left_y, (0., 0., 1., 0.)) if
                     (a+b)*.5 < .5 else (right_t, 1e5, u, right_y, (0., 0., 1., 0.))
                     for a,b in zip(edges[:-1], edges[1:]))
    labels = tuple('LEFT' if (a+b)*.5 < .5 else 'RIGHT' for a,b in zip(edges[:-1], edges[1:]))
    state = RegionalDuctState.from_physical(geometry, mesh, edges, physical, labels, _thermo())
    return state


def _boundary_flux(kernel, state):
    U = np.asarray(state.inventory)/np.asarray(state.volumes)[:, None]
    primitive = kernel.recover(state).V
    return np.stack((kernel.physical_flux(U[0], primitive[0]),
                     kernel.physical_flux(U[-1], primitive[-1])))


def _plain(value):
    """Convert the checkpoint boundary to JSON primitives only."""
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, dict):
        return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_plain(item) for item in value]
    return value


def _atomic_json(path, value):
    """Commit a complete restart record, never a partially written JSON file."""
    path = Path(path)
    temporary = path.with_name(path.name + '.tmp')
    with temporary.open('w', encoding='utf-8') as stream:
        json.dump(_plain(value), stream, sort_keys=True, separators=(',', ':'))
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def _restart_sources():
    """Every implementation and immutable input consumed by a restart."""
    data = ROOT/'docs/science/C1.0/datasets'
    paths = (Path(__file__), ROOT/'validation/fixtures/VAL-008/execution.py',
             ROOT/'validation/fixtures/VAL-008/input.json',
             ROOT/'src/dino2next/__init__.py',
             ROOT/'src/dino2next/config/__init__.py',
             ROOT/'src/dino2next/gasdynamics/__init__.py',
             ROOT/'src/dino2next/gasdynamics/regional.py',
             ROOT/'src/dino2next/geometry/__init__.py',
             ROOT/'src/dino2next/numerics/__init__.py',
             ROOT/'src/dino2next/numerics/regional.py',
             ROOT/'src/dino2next/provenance/__init__.py',
             ROOT/'src/dino2next/thermo/__init__.py',
             ROOT/'src/dino2next/units/__init__.py',
             ROOT/'src/dino2next/volumes/__init__.py',
             data/'thermo_runtime_continuous_v1.json', data/'thermo_species.json',
             data/'thermo_transport.yaml', ROOT/'research/bcr_s03_nasa_inversion/generate.py')
    return {str(path.relative_to(ROOT)): sha256(path.read_bytes()).hexdigest() for path in paths}


def _journal_prefix(path, length):
    """Read and authenticate exactly the checkpoint-owned journal prefix."""
    if length < 0 or path.stat().st_size < length:
        raise ValueError('Restart step journal is truncated before its committed offset')
    digest = sha256(); records = 0; remaining = length
    with path.open('rb') as stream:
        while remaining:
            chunk = stream.read(min(1024*1024, remaining))
            if not chunk:
                raise ValueError('Restart step journal ended before its committed offset')
            digest.update(chunk); records += chunk.count(b'\n'); remaining -= len(chunk)
    return digest, records


def run_contact(case, n, cfl, *, guard_cells, end_time=None, samples=101, profile=False,
                checkpoint_path=None, resume=False, checkpoint_steps=1, stop_after_steps=None):
    """Advance a contact with W/I12 and return physical regional observations.

    This function intentionally has no reference import. The caller supplies the
    frozen contact declaration; references remain assessment-only.
    """
    if not 0 < cfl <= .2:
        raise ValueError('MR-008 permits only the declared CFL range')
    if checkpoint_steps != 1:
        raise ValueError('checkpoint_steps must be positive')
    target_time = float(case['time'] if end_time is None else end_time)
    if not 0 < target_time <= float(case['time']):
        raise ValueError('Contact sample time must stay within the frozen fixture')
    if resume and checkpoint_path is None:
        raise ValueError('A restart requires an explicit checkpoint path')
    source_bindings = _restart_sources()
    driver_sha = source_bindings[str(Path(__file__).relative_to(ROOT))]
    restart_config = dict(schema='VAL-008-regional-restart-1', case=case, N=int(n), CFL=float(cfl),
                          guard_cells=int(guard_cells), target_time=target_time, samples=int(samples),
                          driver_sha256=driver_sha, source_bindings=source_bindings)
    checkpoint_path = None if checkpoint_path is None else Path(checkpoint_path)
    audit_path = None if checkpoint_path is None else checkpoint_path.with_suffix('.steps.jsonl')
    trial_path = None if checkpoint_path is None else checkpoint_path.with_suffix('.trials.jsonl')
    if checkpoint_path is not None:
        checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
    state = initial_state(case, n, guard_cells)
    kernel = RegionalNumericalKernel(state.thermo)
    times = np.linspace(0., target_time, samples)
    output = [state]
    ledgers = []
    # These ledgers are accumulated from the same committed face/source
    # integrals that advance I.  They deliberately remain independent of the
    # reference solution and retain the original [0, 1] measurement window.
    def inventory(current, indices):
        return np.sum(np.asarray(current.inventory)[indices], axis=0)
    def window_inventory(current):
        # A fixed physical window may cut a material region, so its inventory
        # must be its W-overlap projection, never an all-or-nothing region sum.
        return np.asarray(current.projection((0., 1.)).conservative_projection[0])
    def physical_flux(current, x):
        edges = np.asarray(current.edges)
        cell = min(len(current.labels)-1, max(0, int(np.searchsorted(edges, x, side='right')-1)))
        U = np.asarray(current.inventory)[cell]/np.asarray(current.volumes)[cell]
        primitive = kernel.recover(current)
        return kernel.physical_flux(U, primitive.V[cell])
    full_initial = inventory(state, np.arange(len(state.labels)))
    window_initial = window_inventory(state)
    full_external = np.zeros(12); full_sources = np.zeros(12); full_throughput = np.zeros(12)
    window_external = np.zeros(12); window_sources = np.zeros(12); window_throughput = np.zeros(12)
    ledger_samples = []
    guard_audit = []
    causal_audit = []
    step_audit = []
    # Rejected trials have no committed state or ledger, but remain durable
    # evidence of the global transaction's dt recovery.
    trials = []
    timing = dict(rhs=0., timestep=0., proposal=0., causal=0., remap=0., audit=0., persistence=0.)
    progress = dict(accepted_steps=0, rejected_steps=0, minimum_dt=float('inf'), minimum_volume=float('inf'), maximum_regions=0,
                    guard_candidates=0, guard_high_rejected=0, guard_bisection_evaluations=0,
                    minimum_selected_guard=1.)
    def snapshot(current):
        ledger_samples.append(dict(
            full=dict(initial=full_initial.copy(), inventory=inventory(current, np.arange(len(current.labels))),
                      external=full_external.copy(), sources=full_sources.copy(), throughput=full_throughput.copy()),
            window=dict(initial=window_initial.copy(), inventory=window_inventory(current),
                        external=window_external.copy(), sources=window_sources.copy(), throughput=window_throughput.copy())))
    def checkpoint(next_sample, *, incomplete=False):
        if checkpoint_path is None:
            return
        tick = perf_counter()
        # The append is durable before the atomic pointer moves to it.  A
        # restart truncates any record written after the last committed pointer.
        stream.flush(); trial_stream.flush()
        os.fsync(stream.fileno()); os.fsync(trial_stream.fileno())
        _atomic_json(checkpoint_path, dict(config=restart_config, incomplete=bool(incomplete),
            time=float(time), next_sample=int(next_sample), state=state.to_restart(),
            output=[item.to_restart() for item in output], ledger_samples=ledger_samples,
            full_initial=full_initial, window_initial=window_initial,
            full_external=full_external, full_sources=full_sources, full_throughput=full_throughput,
            window_external=window_external, window_sources=window_sources, window_throughput=window_throughput,
            progress=progress, timing=timing, audit_offset=stream.tell(),
            audit_sha256=audit_digest.hexdigest(), audit_records=audit_records,
            trial_offset=trial_stream.tell(), trial_sha256=trial_digest.hexdigest(),
            trial_records=trial_records))
        timing['persistence'] += perf_counter()-tick

    stream = None
    audit_digest = sha256()
    audit_records = 0
    trial_stream = None
    trial_digest = sha256()
    trial_records = 0
    next_sample = 1
    time = 0.
    if resume:
        if not checkpoint_path.is_file():
            raise ValueError('Restart checkpoint is unavailable')
        payload = json.loads(checkpoint_path.read_text(encoding='utf-8'))
        if payload.get('config') != restart_config:
            raise ValueError('Restart code, fixture, or configuration identity differs')
        if not audit_path.is_file() or not trial_path.is_file():
            raise ValueError('Restart step journal is unavailable')
        audit_digest, audit_records = _journal_prefix(audit_path, int(payload['audit_offset']))
        if (payload.get('audit_sha256') != audit_digest.hexdigest()
                or payload.get('audit_records') != audit_records):
            raise ValueError('Restart step journal prefix identity differs from checkpoint')
        trial_digest, trial_records = _journal_prefix(trial_path, int(payload['trial_offset']))
        if (payload.get('trial_sha256') != trial_digest.hexdigest()
                or payload.get('trial_records') != trial_records):
            raise ValueError('Restart rejected-trial journal prefix identity differs from checkpoint')
        with trial_path.open('rb') as recovery:
            trials = [json.loads(line) for line in recovery.read(int(payload['trial_offset'])).splitlines()]
        state = type(state).from_restart(payload['state'], state.thermo)
        output = [type(state).from_restart(item, state.thermo) for item in payload['output']]
        ledger_samples = payload['ledger_samples']
        full_initial = np.asarray(payload['full_initial']); window_initial = np.asarray(payload['window_initial'])
        full_external = np.asarray(payload['full_external']); full_sources = np.asarray(payload['full_sources'])
        full_throughput = np.asarray(payload['full_throughput']); window_external = np.asarray(payload['window_external'])
        window_sources = np.asarray(payload['window_sources']); window_throughput = np.asarray(payload['window_throughput'])
        progress = payload['progress']; timing = payload['timing']; time = float(payload['time'])
        next_sample = int(payload['next_sample'])
        with audit_path.open('r+b') as recovery:
            recovery.truncate(int(payload['audit_offset']))
        with trial_path.open('r+b') as recovery:
            recovery.truncate(int(payload['trial_offset']))
    if checkpoint_path is not None:
        stream = audit_path.open('ab+')
        trial_stream = trial_path.open('ab+')
    else:
        class _NullStream:
            def flush(self): pass
            def write(self, value): return len(value)
            def fileno(self): return os.open(os.devnull, os.O_RDONLY)
            def tell(self): return 0
        stream = _NullStream()
        trial_stream = _NullStream()
    if not resume:
        snapshot(state)
        checkpoint(next_sample)
    def record_step(attempt, parent_identity, remapped, dt, faces, stage_faces, sources, causal):
        nonlocal audit_records
        entry = dict(step=int(progress['accepted_steps']), time=float(time), dt=float(dt),
            parent=parent_identity, child=attempt.state.state_identity, remapped_identity=remapped.state_identity,
            W_before=list(state.W), W_after=list(attempt.state.W), remapped_W=list(remapped.W),
            labels_before=list(state.labels), labels_after=list(attempt.state.labels),
            remapped_labels=list(remapped.labels), I_before=np.asarray(state.inventory).tolist(),
            I_after=np.asarray(attempt.state.inventory).tolist(), remapped_I=np.asarray(remapped.inventory).tolist(),
            face_integrals=faces.tolist(), face_stage_integrals=stage_faces.tolist(), source_integrals=sources.tolist(),
            guards=[repr(item) for item in attempt.diagnostics if isinstance(item, tuple) and item and item[0] == 'guard_candidate'],
            causal=causal, diagnostics=[repr(item) for item in attempt.diagnostics])
        if checkpoint_path is None:
            step_audit.append(entry); guard_audit.append(tuple(entry['guards'])); causal_audit.append(tuple(causal))
        else:
            encoded = (json.dumps(_plain(entry), sort_keys=True, separators=(',', ':'))+'\n').encode('utf-8')
            stream.write(encoded); audit_digest.update(encoded); audit_records += 1

    while next_sample < len(times):
        target = times[next_sample]
        while time < target:
            tick = perf_counter()
            rhs = kernel.rhs(state, time, boundary_flux=_boundary_flux(kernel, state))
            timing['rhs'] += perf_counter()-tick
            tick = perf_counter()
            bound, detail = kernel.timestep_bounds(state, rhs)
            dt = min((cfl/.2)*bound, float(target-time))
            timing['timestep'] += perf_counter()-tick
            # The selected transaction restores Yn on every rejected trial,
            # halves dt, and exposes no trial ledger.  A regional route is a
            # consumer of that rule; it must not mistake a stage predictor
            # rejection for a terminal fixture failure.
            for retry in range(17):
                tick = perf_counter()
                attempt = kernel.propose_step(state,
                    lambda candidate, stage_time: kernel.rhs(candidate, stage_time,
                        boundary_flux=_boundary_flux(kernel, candidate)), time, dt)
                timing['proposal'] += perf_counter()-tick
                if attempt.accepted:
                    break
                progress['rejected_steps'] += 1
                trial = dict(time=float(time), dt=float(dt), retry=int(retry),
                             rejection=attempt.rejection,
                             diagnostics=[repr(item) for item in attempt.diagnostics])
                trials.append(trial)
                encoded = (json.dumps(_plain(trial), sort_keys=True, separators=(',', ':'))+'\n').encode('utf-8')
                trial_stream.write(encoded); trial_digest.update(encoded); trial_records += 1
                # Persist the rollback and its diagnostics before another
                # attempt, while the checkpoint still points to the last
                # accepted W/I12 state and journal prefix.
                checkpoint(next_sample)
                if retry == 16:
                    raise RuntimeError(('ADMISSIBILITY_RETRY_EXHAUSTED', attempt.rejection,
                                        tuple(trials[-17:])))
                dt *= .5
            progress['accepted_steps'] += 1
            progress['minimum_dt'] = min(progress['minimum_dt'], float(dt))
            progress['minimum_volume'] = min(progress['minimum_volume'], float(np.min(state.volumes)))
            progress['maximum_regions'] = max(progress['maximum_regions'], len(state.labels))
            tick = perf_counter()
            guards = [item for item in attempt.diagnostics if isinstance(item, tuple) and item and item[0] == 'guard_candidate']
            if len(guards) < 2:
                raise RuntimeError(('REGIONAL_GUARD_AUDIT_INCOMPLETE', attempt.diagnostics))
            progress['guard_candidates'] += len(guards)
            progress['guard_high_rejected'] += sum(item[2] == 1. and not item[3] for item in guards)
            progress['guard_bisection_evaluations'] += sum(0. < item[2] < 1. for item in guards)
            selected = [item for item in attempt.diagnostics if isinstance(item, tuple) and item and item[0] == 'selected_guards']
            if len(selected) != 1:
                raise RuntimeError(('REGIONAL_GUARD_SELECTION_AUDIT_INCOMPLETE', attempt.diagnostics))
            progress['minimum_selected_guard'] = min(progress['minimum_selected_guard'], *selected[0][1])
            causal = []
            for stage_name, stage_state in zip(('Y0', 'Y1', 'Y2', 'FINAL'), attempt.stage_states):
                recovered = kernel.recover(stage_state)
                speed = float(np.max(np.abs(recovered.V[:, 1]) + recovered.a))
                if speed > 1293. + 256*np.finfo(float).eps:
                    raise RuntimeError(('SETUP_CAUSAL_BOUND_FAILED', stage_name, speed, 1293.))
                causal.append(dict(stage=stage_name, max_speed=speed, bound=1293.))
            timing['causal'] += perf_counter()-tick
            tick = perf_counter()
            ledgers.append((attempt.face_integrals, attempt.source_integrals))
            faces = np.asarray(attempt.face_integrals)
            stage_faces = np.asarray(attempt.face_stage_integrals)
            sources = np.asarray(attempt.source_integrals)
            full_external += faces[0] - faces[-1]
            full_throughput += np.sum(abs(stage_faces[:, 0]), axis=0) + np.sum(abs(stage_faces[:, -1]), axis=0)
            full_sources += np.sum(sources, axis=0)
            # The fixed x=0,1 window cuts coarse material regions.  Its
            # exchange is the SSPRK2 average of actual physical face fluxes,
            # not a surrogate regional face chosen by index.
            left = int(np.flatnonzero(np.isclose(np.asarray(state.edges), 0., rtol=0., atol=32*np.finfo(float).eps))[0])
            right = int(np.flatnonzero(np.isclose(np.asarray(state.edges), 1., rtol=0., atol=32*np.finfo(float).eps))[0])
            window_external += faces[left] - faces[right]
            window_throughput += np.sum(abs(stage_faces[:, left]), axis=0) + np.sum(abs(stage_faces[:, right]), axis=0)
            # VAL-008 has A=1, hence its physical area source is identically
            # zero on every partial overlap.
            parent_identity = state.state_identity
            remapped = kernel.reorganize(attempt.state)
            timing['remap'] += perf_counter()-tick
            tick = perf_counter()
            record_step(attempt, parent_identity, remapped, dt, faces, stage_faces, sources, causal)
            timing['audit'] += perf_counter()-tick
            state = remapped
            time = float(target) if dt == target-time else time+dt
            checkpoint(next_sample)
            if stop_after_steps is not None and progress['accepted_steps'] >= stop_after_steps:
                checkpoint(next_sample, incomplete=True)
                if checkpoint_path is not None:
                    stream.close(); trial_stream.close()
                return dict(classification='INCOMPLETE_STOPPED_FOR_RESTART', incomplete=True, times=times[:next_sample],
                    states=tuple(output), ledgers=tuple(ledgers), ledger_samples=tuple(ledger_samples),
                    trials=tuple(trials), guard_audit=tuple(guard_audit), causal_audit=tuple(causal_audit),
                    step_audit=tuple(step_audit), step_audit_path=str(audit_path) if audit_path else None,
                    trial_audit_path=str(trial_path) if trial_path else None,
                    kernel_identity=kernel.identity, source_sha256=driver_sha,
                    profile=dict(timing=timing, progress=progress) if profile else None)
        output.append(state)
        snapshot(state)
        next_sample += 1
        checkpoint(next_sample)
    if checkpoint_path is not None:
        stream.close(); trial_stream.close()
    return dict(classification='NUMERICAL_FIXTURE_ONLY_REGIONAL_CANDIDATE_NOT_ACCEPTANCE',
                times=times, states=tuple(output), ledgers=tuple(ledgers), ledger_samples=tuple(ledger_samples),
                trials=tuple(trials), guard_audit=tuple(guard_audit), causal_audit=tuple(causal_audit), step_audit=tuple(step_audit),
                step_audit_path=str(audit_path) if audit_path else None,
                trial_audit_path=str(trial_path) if trial_path else None,
                kernel_identity=kernel.identity, source_sha256=driver_sha,
                profile=dict(timing=timing, progress=progress) if profile else None)


def pressure_observation(state, edges):
    """Return the explicitly physical p/T observation over fixed base cells."""
    projection = state.projection(edges)
    temperatures = []
    for left, right in zip(projection.W[:-1], projection.W[1:]):
        pieces = [(j, min(right, b)-max(left, a)) for j, (a, b) in
                  enumerate(zip(state.W[:-1], state.W[1:])) if min(right, b)>max(left, a)]
        temperatures.append(sum(state.regional_states.T[j]*width for j, width in pieces)/(right-left))
    return dict(pressure=np.asarray(projection.pressure_volume_average),
                temperature=np.asarray(temperatures), velocity=np.asarray(projection.bulk_velocity),
                conservative=np.asarray(projection.conservative_projection),
                state_identity=projection.state_identity)

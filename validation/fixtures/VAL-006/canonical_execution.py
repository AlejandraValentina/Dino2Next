"""S06 mathematical fixture execution, never a production boundary model."""
import importlib.util
import json
from hashlib import sha256
from pathlib import Path
import time as clock
import platform
import subprocess
from math import fsum

import numpy as np

from dino2next.gasdynamics import Mesh1D, PolynomialSegment
from dino2next.numerics import NumericalKernel, StageRHS

ROOT = Path(__file__).resolve().parents[3]


def compensated(rows):
    return np.array([fsum(column) for column in np.asarray(rows).T])


def module(path):
    path = ROOT / path
    spec = importlib.util.spec_from_file_location('fixture_'+sha256(str(path).encode()).hexdigest()[:12], path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def pack(conserved):
    """Five chemistry slots: pure mathematical carrier N2; common origin R."""
    result = np.zeros((len(conserved), 12))
    result[:, :3] = conserved
    result[:, 5] = result[:, 0]
    result[:, 10] = result[:, 0]
    return result


def reference_parameters(case):
    return {k: case[k] for k in ('speed', 'epsilon', 'kind', 'smooth') if k in case}


def make_mesh(n, nozzle=False):
    edges = tuple(map(float, np.linspace(0, 1, n+1)))
    if nozzle:
        return Mesh1D.from_segments(edges, (PolynomialSegment(0., 1., (1.1, -.4, .4), (1.,)),),
                                    segment_boundaries=(), component_id='VAL-011')
    return Mesh1D(edges, (1.,)*n, (1.,)*(n+1), (1.,)*n)


def setup(fixture_id, n, case):
    eos = module('validation/fixtures/VAL-006/gamma_adapter.py').CanonicalGamma()
    kernel = NumericalKernel(eos, source_kind='NUMERICAL_FIXTURE_ONLY')
    mesh = make_mesh(n, fixture_id == 'VAL-011')
    reference = module(f'validation/references/{fixture_id}/reference.py')
    initial = reference.cell_averages(mesh.cell_bounds, 0., **reference_parameters(case))
    state = kernel.state(mesh, pack(initial['conserved']))
    return kernel, state, reference


class CanonicalRHS:
    """Caller-owned canonical boundary data and accepted geometric source.

    Rigid walls reflect velocity. The free acoustic case uses the explicitly
    prescribed linear invariants around rho=p=1, not a nonlinear reservoir.
    Smooth nozzle ghost points are evaluated at their actual exterior positions.
    """
    def __init__(self, kernel, fixture_id, case, reference):
        self.kernel, self.fixture_id, self.case, self.reference = kernel, fixture_id, case, reference
        self.limiter_records = []

    def __call__(self, state, time):
        k = self.kernel
        U = state.Q / np.asarray(state.mesh.area_averages)[:, None]
        periodic = self.fixture_id in ('VAL-009', 'VAL-027')
        if periodic:
            faces = k.reconstruct(state, boundary='periodic')
            flux = k.interior_flux(faces)
        else:
            V = k.recover(U).V
            left, right = np.repeat(U[:1], 4, axis=0), np.repeat(U[-1:], 4, axis=0)
            rigid = (self.fixture_id == 'VAL-010' and self.case['kind'] == 'rigid') or (
                self.fixture_id == 'VAL-011' and not self.case['smooth'])
            free = self.fixture_id == 'VAL-010' and self.case['kind'] == 'free'
            smooth = self.fixture_id == 'VAL-011' and self.case['smooth']
            if rigid:
                left, right = U[:4][::-1].copy(), U[-4:][::-1].copy()
                left[:, 1] *= -1
                right[:, 1] *= -1
            elif smooth:
                dx = state.mesh.dx[0]
                left = pack(self.reference.point_states(np.arange(-4, 0)*dx+dx/2, smooth=True)['conserved'])
                right = pack(self.reference.point_states(1+np.arange(4)*dx+dx/2, smooth=True)['conserved'])
            elif free:
                # Reflection of p' and rho' at right; zero incoming invariant
                # at left. Extrapolated outgoing invariant is stage-dependent.
                c = np.sqrt(1.4)
                vl, vr = V[:4][::-1].copy(), V[-4:][::-1].copy()
                outgoing = vl[:, 1]-(vl[:, 2]-1)/c
                vl[:, 1] = outgoing/2
                vl[:, 2] = 1-c*outgoing/2
                vl[:, 0] = 1+(vl[:, 2]-1)/c**2
                vr[:, 2] = 2-vr[:, 2]
                vr[:, 0] = 1+(vr[:, 2]-1)/c**2
                left, right = k.primitive_to_conservative(vl), k.primitive_to_conservative(vr)
            faces = k.reconstruct(state, boundary='physical', ghosts=(left, right))
            if rigid:
                inside = np.stack((faces.right[0], faces.left[-1]))
                mirror = inside.copy(); mirror[:, 1] *= -1
                wall = k.hllc(np.stack((mirror[0], inside[1])), np.stack((inside[0], mirror[1])))
                prescribed = np.zeros((2, 12)); prescribed[:, 1] = wall[:, 1]
            elif smooth:
                prescribed = k.physical_flux(pack(self.reference.point_states(np.array([0., 1.]), smooth=True)['conserved']))
            elif free:
                v = k.recover(np.stack((faces.right[0], faces.left[-1]))).V.copy()
                outgoing_left = v[0, 1]-(v[0, 2]-1)/c
                outgoing_right = v[1, 1]+(v[1, 2]-1)/c
                v[0, 1], v[0, 2] = outgoing_left/2, 1-c*outgoing_left/2
                v[1, 1], v[1, 2] = outgoing_right, 1.
                v[:, 0] = 1+(v[:, 2]-1)/c**2
                prescribed = k.physical_flux(k.primitive_to_conservative(v))
            else:
                prescribed = k.physical_flux(np.stack((U[0], U[-1])))
            flux = k.interior_flux(faces, boundary_flux=prescribed)
        sources = np.zeros_like(state.Q)
        if self.fixture_id == 'VAL-011':
            sources[:, 1] = k.recover(U).V[:, 2]*np.diff(state.mesh.face_areas)/np.asarray(state.mesh.dx)
        # flattening is the remaining slope multiplier: one is inactive.
        active = np.flatnonzero((faces.contraction < 1) | (faces.flattening < 1) | faces.near)
        if len(active) or np.any(flux.flux_b):
            self.limiter_records.append(dict(time=time, cells=active.tolist(),
                contraction=faces.contraction[active].tolist(), flattening=faces.flattening[active].tolist(),
                near=faces.near[active].tolist(), flux_b=np.flatnonzero(flux.flux_b).tolist()))
        return StageRHS(flux, sources)


def execute(fixture_id, n, case, cfl, *, output_root=None):
    k, state, reference = setup(fixture_id, n, case)
    rhs = CanonicalRHS(k, fixture_id, case, reference)
    dx = np.asarray(state.mesh.dx)
    initial_inventory = compensated(state.Q*dx[:, None])
    initial_primitive = k.recover(state.Q/np.asarray(state.mesh.area_averages)[:,None])
    sensible_scale = fsum(state.Q[:,0]*initial_primitive.cv*initial_primitive.T*dx)
    boundary_terms, source_terms, throughput = [], [], []
    initial_ref = reference.cell_averages(state.mesh.cell_bounds, 0., **reference_parameters(case))
    reference_samples = [np.column_stack([initial_ref[name] for name in ('rho','u','p')])]
    samples, times, steps, rejected, metrics = [state.Q.copy()], [0.], [], [], []
    # Initial sample is measured too: initialization/recovery roundoff is not
    # silently treated as an exact candidate state.
    initial_error = abs(initial_primitive.V[:, :3]-reference_samples[0])
    metrics.append(dict(time=0., L1=np.sum(dx[:,None]*initial_error,axis=0).tolist(),
        L2=np.sqrt(np.sum(dx[:,None]*initial_error**2,axis=0)).tolist(),
        Linf=initial_error.max(axis=0).tolist(), ledger=np.zeros(12).tolist(),
        inventory=initial_inventory.tolist(), boundary=np.zeros(12).tolist(), source=np.zeros(12).tolist()))
    start = clock.monotonic()
    end = case['time']; time = 0.
    for target in np.linspace(0., end, 101)[1:]:
        while time < target:
            primitive = k.recover(state.Q/np.asarray(state.mesh.area_averages)[:, None])
            dt = min(float(cfl*np.min(dx/(abs(primitive.V[:, 1])+primitive.a))), float(target-time))
            for retry in range(17):
                attempt = k.propose_step(state, rhs, float(time), float(dt))
                if attempt.accepted:
                    break
                rejected.append(dict(time=time, dt=dt, reason=attempt.rejection, diagnostics=attempt.diagnostics))
                if attempt.rejection not in ('LOW_ORDER_STAGE_INADMISSIBLE_RETRY_DT', 'FLUX_LIMIT_ROUND_OFF_RETRY_DT'):
                    raise AssertionError(f'{fixture_id}: {attempt.rejection}: {attempt.diagnostics}')
                dt /= 2
                if time+dt == time:
                    raise AssertionError('No representable admissible step')
            else:
                failure = ROOT/'artifacts'/fixture_id/f"{case['name']}-N{n}-CFL{cfl}-failed.json"
                failure.parent.mkdir(parents=True, exist_ok=True)
                failure.write_text(json.dumps(dict(result='FAIL', reason='RETRY_LIMIT_REACHED',
                    time=time, attempts=rejected), indent=2)+'\n', encoding='utf-8')
                raise AssertionError('RETRY_LIMIT_REACHED: initial attempt plus 16 retries failed')
            state = attempt.state
            time = float(target) if dt == target-time else time+dt
            steps.append(dict(time=time, dt=dt, diagnostics=attempt.diagnostics))
            boundary_terms.append(attempt.face_integrals[0]-attempt.face_integrals[-1])
            source_terms.append(compensated(attempt.source_integrals))
            throughput.append(abs(attempt.face_integrals[0])+abs(attempt.face_integrals[-1])+
                              compensated(abs(attempt.source_integrals)))
        samples.append(state.Q.copy()); times.append(time)
        p = k.recover(state.Q/np.asarray(state.mesh.area_averages)[:, None]).V[:, :3]
        ref = reference.cell_averages(state.mesh.cell_bounds, time, **reference_parameters(case))
        r = np.column_stack([ref[name] for name in ('rho', 'u', 'p')])
        reference_samples.append(r)
        err = abs(p-r)
        inventory = compensated(state.Q*dx[:, None])
        external = compensated(boundary_terms); sources = compensated(source_terms)
        residual = compensated(np.stack((inventory, -initial_inventory, -external, -sources)))
        # Explicit nonzero canonical density/velocity/energy reference scales;
        # species/tracer scales are total initial mass, never zero partial mass.
        scales = np.full(12, initial_inventory[0]); scales[1] *= np.sqrt(1.4)
        scales[2] = sensible_scale
        ledger_scale = abs(initial_inventory)+compensated(throughput)+scales
        metrics.append(dict(time=time, L1=np.sum(dx[:, None]*err, axis=0).tolist(),
                            L2=np.sqrt(np.sum(dx[:, None]*err**2, axis=0)).tolist(),
                            Linf=err.max(axis=0).tolist(), ledger=(residual/ledger_scale).tolist(),
                            inventory=inventory.tolist(), boundary=external.tolist(), source=sources.tolist()))
    output_root = Path(output_root) if output_root else ROOT/'artifacts'/fixture_id
    output_root.mkdir(parents=True, exist_ok=True)
    name = f"{case['name']}-N{n}-CFL{cfl}"
    raw = output_root/(name+'.npz')
    np.savez_compressed(raw, times=times, Q=samples, reference_rho_u_p=reference_samples,
                        cell_bounds=state.mesh.cell_bounds)
    record = dict(fixture=fixture_id, classification='NUMERICAL_FIXTURE_ONLY', N=n, CFL=cfl, case=case,
                  metrics=metrics, steps=steps, rejections=rejected, limiter_records=rhs.limiter_records,
                  elapsed_seconds=clock.monotonic()-start, raw_sha256=sha256(raw.read_bytes()).hexdigest(),
                  source_sha256=sha256(Path(__file__).read_bytes()).hexdigest(),
                  environment=dict(python=platform.python_version(), numpy=np.__version__),
                  commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
                  hashes={str(p.relative_to(ROOT)):sha256(p.read_bytes()).hexdigest() for p in [
                      ROOT/'src/dino2next/numerics/__init__.py', ROOT/f'validation/references/{fixture_id}/reference.py',
                      ROOT/f'validation/fixtures/{fixture_id}/input.json', Path(__file__).with_name('gamma_adapter.py')]},
                  result='EXECUTED_METRICS_PENDING_ASSESSMENT')
    (output_root/(name+'.json')).write_text(json.dumps(record, indent=2)+'\n', encoding='utf-8')
    return record, state, reference

def execute(fixture_id, n, case, cfl, *, output_root=None):
    k, state, reference = setup(fixture_id, n, case)
    rhs = CanonicalRHS(k, fixture_id, case, reference)
    rhs.limiter_records = STREAM_SINKS['limiters']
    dx = np.asarray(state.mesh.dx)
    initial_inventory = compensated(state.Q*dx[:, None])
    initial_primitive = k.recover(state.Q/np.asarray(state.mesh.area_averages)[:,None])
    sensible_scale = fsum(state.Q[:,0]*initial_primitive.cv*initial_primitive.T*dx)
    boundary_terms, source_terms, throughput = [], [], []
    initial_ref = reference.cell_averages(state.mesh.cell_bounds, 0., **reference_parameters(case))
    reference_samples = [np.column_stack([initial_ref[name] for name in ('rho','u','p')])]
    samples, times, steps, rejected, metrics = [state.Q.copy()], [0.], STREAM_SINKS['steps'], STREAM_SINKS['rejections'], []
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
                failure = Path(output_root)/f"{case['name']}-N{n}-CFL{cfl}-failed.json"
                failure.parent.mkdir(parents=True, exist_ok=True)
                failure.write_text(json.dumps(dict(result='FAIL', reason='RETRY_LIMIT_REACHED',
                    time=time, attempts=rejected.manifest()), indent=2)+'\n', encoding='utf-8')
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
                  metrics=metrics, steps=steps.manifest(), rejections=rejected.manifest(), limiter_records=rhs.limiter_records.manifest(),
                  elapsed_seconds=clock.monotonic()-start, raw_sha256=sha256(raw.read_bytes()).hexdigest(),
                  source_sha256=STREAM_SOURCE_HASH, canonical_source_sha256=sha256(Path(__file__).read_bytes()).hexdigest(), storage='STREAMED_TRACES_EXPERIMENTAL',
                  environment=dict(python=platform.python_version(), numpy=np.__version__),
                  commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
                  hashes={str(p.relative_to(ROOT)):sha256(p.read_bytes()).hexdigest() for p in [
                      ROOT/'src/dino2next/numerics/__init__.py', ROOT/f'validation/references/{fixture_id}/reference.py',
                      ROOT/f'validation/fixtures/{fixture_id}/input.json', Path(__file__).with_name('gamma_adapter.py')]},
                  result='EXECUTED_METRICS_PENDING_ASSESSMENT')
    (output_root/(name+'.json')).write_text(json.dumps(record, indent=2)+'\n', encoding='utf-8')
    return record, state, reference

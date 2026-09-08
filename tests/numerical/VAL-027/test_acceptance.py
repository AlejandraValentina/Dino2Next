"""Actual R4 temporal verification and exact-real contact reference certificate."""
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import platform
import numpy as np

ROOT=Path(__file__).resolve().parents[3]

def load_driver():
    spec=importlib.util.spec_from_file_location('canonical_driver',ROOT/'validation/fixtures/VAL-006/canonical_execution.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def _run_temporal_reference_and_five_actual_step_sequences():
    driver=load_driver();fixture_path=ROOT/'validation/fixtures/VAL-027/input.json'
    assert sha256(fixture_path.read_bytes()).hexdigest()=='688b23f9153b2204eac36fd8dee562b9a284772ad734eef5995ba7535a8a60d1'
    fixture=json.loads(fixture_path.read_text());source=ROOT/fixture['frozen_source']
    expected_path=ROOT/'validation/expected/VAL-027/acceptance.json'
    expected=json.loads(expected_path.read_text())
    assert expected['source_sha256']==fixture['frozen_source_sha256']
    assert expected['thresholds']==dict(finest_density_L1_max=1e-10,first_two_order_min=1.8,first_two_order_max=2.2,reference_discrepancy_max=1e-11)
    assert sha256(source.read_bytes()).hexdigest()==fixture['frozen_source_sha256']
    assert fixture['frozen_fiche']==json.loads(source.read_text())['fixtures']['VAL-027']
    assert fixture['baseline']=='C1.0-R4' and fixture['dt']==[.002,.001,.0005,.00025,.000125]
    out=ROOT/'artifacts/VAL-027';out.mkdir(parents=True,exist_ok=True)
    reference_dir=ROOT/'validation/references/VAL-027'
    sources=[ROOT/'src/dino2next/numerics/__init__.py',fixture_path,source,expected_path,Path(__file__),
             ROOT/'validation/fixtures/VAL-006/canonical_execution.py',ROOT/'validation/fixtures/VAL-006/gamma_adapter.py',
             *sorted(reference_dir.glob('*.py'))]
    hashes={str(p.relative_to(ROOT)):sha256(p.read_bytes()).hexdigest() for p in sources}
    report=dict(classification='NUMERICAL_VERIFICATION_TEMPORAL_ONLY',baseline='C1.0-R4',N=40,
                result='RUNNING',qualification='PENDING',hashes=hashes,levels=[],
                environment={'python':platform.python_version(),'numpy':np.__version__})
    def save():
        assert hashes=={str(p.relative_to(ROOT)):sha256(p.read_bytes()).hexdigest() for p in sources},'SOURCE_CHANGED_DURING_RUN'
        (out/'acceptance.json').write_text(json.dumps(report,indent=2)+'\n')
    save()
    kernel,initial,reference=driver.setup('VAL-027',40,fixture['cases'][0])
    rhs=driver.CanonicalRHS(kernel,'VAL-027',fixture['cases'][0],reference)
    t,oracle,nfev=reference.integrate(kernel,initial,rhs)
    tc,cross,cross_nfev=reference.integrate(kernel,initial,rhs,crosscheck=True)
    assert oracle.shape==cross.shape==(801,40,12)
    np.testing.assert_array_equal(t,np.arange(801)*.000125);np.testing.assert_array_equal(t,tc)
    discrepancy=float(np.max(abs(oracle-cross)))
    np.savez_compressed(out/'full-kernel-reference.npz',times=t,Q=oracle,cross=cross)
    report.update(reference_cross_difference=discrepancy,nfev=nfev,cross_nfev=cross_nfev)
    save()
    # Cross differences corroborate; only the independent continuous-defect
    # certificate qualifies the reference against the exact-real SV-027 target.
    for name in ('scalar027.py','certify027_residual.py','certify027_target.py'):
        with (out/(name+'.log')).open('w') as log:
            command=[sys.executable,str(reference_dir/name),'--output-dir',str(out)]
            result=subprocess.run(command,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
        if result.returncode:
            report.update(result='REFERENCE_NOT_QUALIFIED',qualification='REFERENCE_NOT_QUALIFIED',failed_command=command);save()
        assert result.returncode==0,('REFERENCE_NOT_QUALIFIED',name,result.returncode)
    certificate_path=out/'contact-target-certificate.json';certificate=json.loads(certificate_path.read_text())
    qualified=certificate['full_reference_all_fields_below_1e_minus_11_exact']
    uncertainty=float(np.nextafter(certificate['full_reference_density_max_L1_error_bound_display'],np.inf))
    report.update(qualification='REFERENCE_QUALIFIED' if qualified else 'REFERENCE_NOT_QUALIFIED',
                  reference_uncertainty_density_L1=uncertainty,reference_certificate_sha256=sha256(certificate_path.read_bytes()).hexdigest())
    save();assert qualified,'REFERENCE_NOT_QUALIFIED'
    for dt in fixture['dt']:
        state=initial;states=[state.Q];diagnostics=[];count=round(.1/dt);stride=800//count
        err=state.Q-oracle[0]
        rows=[dict(time=0.,density_L1=float(np.mean(abs(err[:,0]))),state_L1=np.mean(abs(err),axis=0).tolist(),
                   state_L2=np.sqrt(np.mean(err**2,axis=0)).tolist(),state_Linf=np.max(abs(err),axis=0).tolist())]
        assert stride*count==800
        flux_ledger=np.zeros((41,12));source_ledger=np.zeros((40,12))
        for i in range(count):
            attempt=kernel.propose_step(state,rhs,float(i*dt),dt)
            assert attempt.accepted,(attempt.rejection,attempt.diagnostics)
            stage_records=[d for d in attempt.diagnostics if d[0]=='stage']
            assert len(stage_records)==2 and all(d[3]==1. and d[5]==0 for d in stage_records),'REFERENCE_NOT_QUALIFIED: guard changed compared RHS'
            state=attempt.state;states.append(state.Q);err=state.Q-oracle[(i+1)*stride]
            flux_ledger+=attempt.face_integrals;source_ledger+=attempt.source_integrals
            rows.append(dict(time=(i+1)*dt,density_L1=float(np.mean(abs(err[:,0]))),
                             state_L1=np.mean(abs(err),axis=0).tolist(),state_L2=np.sqrt(np.mean(err**2,axis=0)).tolist(),state_Linf=np.max(abs(err),axis=0).tolist()))
            diagnostics.append(attempt.diagnostics)
        times=np.arange(count+1)*dt;np.testing.assert_array_equal(times,t[::stride])
        np.savez_compressed(out/f'dt-{dt}.npz',times=times,Q=states)
        delta=driver.compensated((state.Q-initial.Q)*np.asarray(state.mesh.dx)[:,None])
        exterior=flux_ledger[0]-flux_ledger[-1];physical_source=driver.compensated(source_ledger)
        residual=delta-exterior-physical_source
        initial_inventory=driver.compensated(initial.Q*np.asarray(state.mesh.dx)[:,None])
        primitive=kernel.recover(initial.Q)
        reference_scale=np.full(12,initial_inventory[0]);reference_scale[1]*=np.sqrt(1.4)
        reference_scale[2]=float(np.sum(initial.Q[:,0]*primitive.cv*primitive.T*np.asarray(state.mesh.dx)))
        scale=abs(initial_inventory)+abs(flux_ledger[0])+abs(flux_ledger[-1])+abs(physical_source)+reference_scale
        report['levels'].append(dict(dt=dt,steps=count,rows=rows,diagnostics=diagnostics,
                                    max_density_L1=max(row['density_L1'] for row in rows),final_density_L1=rows[-1]['density_L1'],
                                    ledger=dict(residual=residual.tolist(),scale=scale.tolist(),normalized=(abs(residual)/scale).tolist(),flux_integral=flux_ledger.tolist(),source_integral=source_ledger.tolist())))
        save()
    errors=[r['max_density_L1'] for r in report['levels']];orders=np.log2(np.asarray(errors[:-1])/errors[1:])
    intervals=[dict(lower=float(np.nextafter(error-uncertainty,-np.inf)) if error>uncertainty else 0.,
                    upper=float(np.nextafter(error+uncertainty,np.inf))) for error in errors]
    floor_qualified=min(errors[:3])>uncertainty
    passed=floor_qualified and np.all(np.isfinite(orders)) and intervals[-1]['upper']<=1e-10 and np.all((orders[:2]>=1.8)&(orders[:2]<=2.2))
    report.update(orders=orders.tolist(),density_error_intervals=intervals,result='PASS' if passed else 'FAIL' if floor_qualified else 'REFERENCE_NOT_QUALIFIED')
    save()
    assert intervals[-1]['upper']<=1e-10
    assert floor_qualified,'REFERENCE_NOT_QUALIFIED: order at certified reference floor'
    assert np.all((orders[:2]>=1.8)&(orders[:2]<=2.2)),orders


def test_temporal_reference_and_five_actual_step_sequences():
    try:
        _run_temporal_reference_and_five_actual_step_sequences()
    except Exception as exc:
        path=ROOT/'artifacts/VAL-027/acceptance.json'
        report=json.loads(path.read_text()) if path.exists() else {}
        report.update(result='REFERENCE_NOT_QUALIFIED' if 'REFERENCE_NOT_QUALIFIED' in str(exc) else 'FAIL',
                      failure=dict(type=type(exc).__name__,message=str(exc)))
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(json.dumps(report,indent=2)+'\n')
        raise

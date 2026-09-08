"""All original NASA contacts/shocks, with SV-008 computational guards."""
from pathlib import Path
import importlib.util
import json
import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[3]


def driver():
    spec = importlib.util.spec_from_file_location('nasa008_execution',ROOT/'validation/fixtures/VAL-008/execution.py')
    obj = importlib.util.module_from_spec(spec); spec.loader.exec_module(obj)
    return obj


@pytest.mark.parametrize('case_index',range(18))
def test_complete_nasa_sequence(case_index):
    d = driver(); fixture = d.verify_fixture(); case = fixture['cases'][case_index]
    rows = []
    out = ROOT/'artifacts/VAL-008'; out.mkdir(parents=True,exist_ok=True)
    path = out/(case['name']+'-assessment.json')
    report = dict(classification='NUMERICAL_VERIFICATION',case=case,result='RUNNING',runs=rows)
    def save(): path.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    save()
    try:
        for n in fixture['meshes'][case['kind']]:
            for cfl in fixture['CFL']:
                record = d.execute(case,n,cfl)
                assert len(record['metrics']) == 101
                rows.append(dict(N=n,CFL=cfl,max_L1=np.max([r['L1'] for r in record['metrics']],axis=0).tolist(),
                    max_L2=np.max([r['L2'] for r in record['metrics']],axis=0).tolist(),
                    max_Linf=np.max([r['Linf'] for r in record['metrics']],axis=0).tolist(),
                    reference_error_bound=record['reference_qualification']['total_normalized_reference_bound'][:3],
                    ledger_max=max(abs(v) for r in record['metrics'] for l in r['ledgers'].values() for v in l['normalized']),
                    raw_sha256=record['raw_sha256']))
                save()
        spatial = [r for r in rows if r['CFL']==.05]
        if case['kind']=='contact':
            thermal = case['parameters']['pair'] != 0
            assert all(np.nextafter(r['max_L1'][2]+r['reference_error_bound'][2],np.inf) <= (2e-3 if thermal else 5e-4) for r in rows)
            assert all(np.nextafter(r['max_Linf'][2]+r['reference_error_bound'][2],np.inf) <= (2e-2 if thermal else 5e-3) for r in rows)
        else:
            errors = np.asarray([r['max_L1'] for r in spatial])
            orders = np.log2(errors[:-1]/errors[1:]); report['orders_rho_u_p']=orders.tolist()
            uncertainty = np.asarray([r['reference_error_bound'] for r in spatial])
            assert np.all(errors>uncertainty), 'REFERENCE_NOT_QUALIFIED: shock order at reference floor'
            lower = np.nextafter(errors-uncertainty,-np.inf)
            upper = np.nextafter(errors+uncertainty,np.inf)
            conservative_orders = np.log2(lower[:-1]/upper[1:])
            report['order_lower_bounds_rho_u_p'] = conservative_orders.tolist()
            assert np.all(np.isfinite(orders)) and np.all(np.diff(errors,axis=0)<0)
            assert np.all(lower[:-1]>upper[1:]) and np.all(conservative_orders[-2:]>=.5), conservative_orders
        assert all(r['ledger_max']<=1e-10 for r in rows)
        # Temporal separation uses actual aligned finest-grid sequences.
        finest = spatial[-1]['N']; raw = [np.load(out/f"{case['name']}-N{finest}-CFL{cfl}.npz") for cfl in fixture['CFL']]
        report['finest_temporal_separation'] = []
        for a,b in zip(raw[:-1],raw[1:]):
            assert np.array_equal(a['times'],b['times'])
            left,right = a['window_indices']; assert np.array_equal(a['window_indices'],b['window_indices'])
            report['finest_temporal_separation'].append(np.max(np.mean(abs(a['Q'][:,left:right]-b['Q'][:,left:right]),axis=1),axis=0).tolist())
        report['result']='PASS'; save()
    except Exception as exc:
        report['result']='FAIL'; report['failure']=repr(exc); save(); raise

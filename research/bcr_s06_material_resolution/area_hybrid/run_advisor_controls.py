"""Actual proposed-step controls on varied positive area and moving contacts."""
from pathlib import Path
from hashlib import sha256
import json,time
import numpy as np
from advisor import AdvisedAreaHybrid
from area_solver import G
from dino2next.gasdynamics import PolynomialSegment
from run_controls import model,physical

HERE=Path(__file__).resolve().parent
rows=[];arrays={};start=time.perf_counter()
for i,coefficients in enumerate(((1.,0.,20.),(4.,-3.,1.),(.1,10.))):
    for u in (30.,-30.):
        grid=np.linspace(0,1,13)
        s=AdvisedAreaHybrid(model(),grid,G.VolumeMap(PolynomialSegment(0.,1.,coefficients,(1.,))))
        initial=s.initialize(grid,physical(grid,u=u),('left',)*6+('right',)*6)
        predictor=s.evaluate_bounds(initial)
        final,ledger,used,failures=s.attempt(initial,predictor['limit'])
        key=f'area{i}-u{u:g}'
        arrays[key+'-initial-W']=initial.W;arrays[key+'-initial-I']=initial.inventory
        arrays[key+'-final-W']=final.W;arrays[key+'-final-I']=final.inventory
        arrays[key+'-faces']=ledger.faces;arrays[key+'-sources']=ledger.sources
        finalprimitive=s.recover(final)
        rows.append(dict(area_coefficients=coefficients,u=u,requested_dt=predictor['limit'],used_dt=used,
            failed_trials=failures,initial_bounds=predictor,advisor_records=s.advisor_records,
            transactions=s.transaction_records,guards=s.guard_records,stages=s.stage_records,
            minimum_final_volume=float(np.diff(final.W).min()),
            temperature_range=[float(finalprimitive[:,4].min()),float(finalprimitive[:,4].max())],
            raw_ledger_residual=(final.inventory.sum(axis=0)-initial.inventory.sum(axis=0)-
                (ledger.faces[0]-ledger.faces[-1])-ledger.sources.sum(axis=0)).tolist()))
raw=HERE/'advisor-controls.npz';np.savez_compressed(raw,**arrays)
report=dict(classification='PROPOSED_VOLUME_ADVISOR_BOUNDED_EXECUTION_NOT_SCIENTIFIC_ACCEPTANCE',
    cases=rows,elapsed_seconds=time.perf_counter()-start,raw_sha256=sha256(raw.read_bytes()).hexdigest(),
    sources={p.name:sha256(p.read_bytes()).hexdigest() for p in [HERE/'advisor.py',HERE/'area_solver.py',Path(__file__)]})
(HERE/'advisor-controls.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'classification':report['classification'],'elapsed_seconds':report['elapsed_seconds'],
    'cases':[{'coefficients':r['area_coefficients'],'u':r['u'],'requested_dt':r['requested_dt'],
              'used_dt':r['used_dt'],'rejected_trials':len(r['failed_trials'])} for r in rows]},indent=2))

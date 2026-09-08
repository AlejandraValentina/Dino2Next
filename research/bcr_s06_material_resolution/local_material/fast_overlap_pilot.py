"""Author-side exact remap search comparison; no evolution or acceptance."""
from pathlib import Path
from hashlib import sha256
import json,time
import numpy as np
from prototype import LocalSolver
from run_controls import make_model
from fast_overlap import experimental_solver,BASELINE_SHA256

HERE=Path(__file__).resolve().parent
Fast=experimental_solver(LocalSolver)
(HERE/'fast-overlap-generated-method.txt').write_text(Fast.overlap_source)
model=make_model();records=[]
cases=[(n,kind) for n in (24,200,800,1600) for kind in ('crossing','thin-slab')]
cases.extend((31,kind) for kind in ('smooth-label','aligned','negative-origin-domain'))
for n,kind in cases:
    grid=np.linspace(-.5,1.5,n+1) if kind=='negative-origin-domain' else np.linspace(0.,1.,n+1)
    left,right=float(grid[0]),float(grid[-1]);dx=float(grid[1]-grid[0])
    shifted=grid.copy()
    if kind!='aligned':shifted[1:-1]+=.23*dx*np.sin(np.linspace(0,np.pi,n+1)[1:-1])
    c=left+.473*(right-left)
    cuts=[] if kind=='smooth-label' else [c]
    if kind=='thin-slab':cuts.append(c+1e-6*dx)
    edges=np.array(sorted(set([*shifted,*cuts])))
    centers=(edges[:-1]+edges[1:])/2
    labels=tuple('homogeneous' if not cuts else ('left' if x<c else 'middle' if kind=='thin-slab' and x<cuts[-1] else 'right') for x in centers)
    physical=[]
    for label,x in zip(labels,centers):
        if kind=='smooth-label':
            y=float(.2+.5*(x-left)/(right-left));Y=(0.,0.,y,1-y,0.);T=800.
        else:Y=(0.,0.,1.,0.,0.) if label!='middle' and label!='right' else (0.,0.,0.,1.,0.);T=600. if Y[2] else 1800.
        physical.append((T,1e5,30.,Y,(0.,0.,1.,0.)))
    old=LocalSolver(model,grid);new=Fast(model,grid)
    state=old.initialize(edges,physical,labels)
    old.recover(state);new.recover(state)
    old.records.clear();new.records.clear()
    outputs=[];rows=[]
    for name,solver in [('original',old),('two-pointer',new)]:
        before=state.edges.tobytes(),state.inventory.tobytes()
        start=time.perf_counter()
        result=solver._transaction('REORGANIZE_SOFTWARE_PILOT',lambda:solver.reorganize(state))
        elapsed=time.perf_counter()-start
        assert before==(state.edges.tobytes(),state.inventory.tobytes())
        outputs.append((result,solver))
        raw=HERE/f'fast-overlap-{n}-{kind}-{name}.npz'
        np.savez_compressed(raw,edges=result.edges,inventory=result.inventory)
        traces={'records':solver.records,'remap_records':solver.remap_records,'transaction_records':solver.transaction_records}
        trace=HERE/f'fast-overlap-{n}-{kind}-{name}-records.json'
        trace.write_text(json.dumps(traces,indent=2)+'\n')
        rows.append(dict(label=name,reorganize_seconds=elapsed,intervals=len(result.labels),
            raw_sha256=sha256(raw.read_bytes()).hexdigest(),trace_sha256=sha256(trace.read_bytes()).hexdigest()))
    a,sa=outputs[0];b,sb=outputs[1]
    assert a.edges.tobytes()==b.edges.tobytes() and a.inventory.tobytes()==b.inventory.tobytes()
    assert a.labels==b.labels and sa.records==sb.records and sa.remap_records==sb.remap_records and sa.transaction_records==sb.transaction_records
    records.append(dict(N=n,kind=kind,bitwise_equal=True,diagnostics_equal=True,runs=rows,
                        speedup=rows[0]['reorganize_seconds']/rows[1]['reorganize_seconds']))
    print(n,kind,rows[0]['reorganize_seconds'],rows[1]['reorganize_seconds'],flush=True)
assert sha256((HERE/'prototype.py').read_bytes()).hexdigest()==BASELINE_SHA256
report=dict(classification='AUTHOR_SOFTWARE_REORGANIZATION_EQUIVALENCE_NOT_NUMERICAL_ACCEPTANCE',
    baseline_sha256=BASELINE_SHA256,helper_sha256=sha256((HERE/'fast_overlap.py').read_bytes()).hexdigest(),
    pilot_sha256=sha256(Path(__file__).read_bytes()).hexdigest(),cases=records)
(HERE/'fast-overlap-report.json').write_text(json.dumps(report,indent=2)+'\n')

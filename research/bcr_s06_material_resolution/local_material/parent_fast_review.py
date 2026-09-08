"""Independent exact-search audit by /root; no evolution or recipe approval."""
from pathlib import Path
from hashlib import sha256
import json
import numpy as np
from fast_overlap import MonotoneTargets

h=Path(__file__).resolve().parent
assert sha256((h/'fast_overlap.py').read_bytes()).hexdigest()=='3a7a9f5f76d8f7eec0ea35589c6b749836b9e0e7107233231a0bdf66e517dd28'
rng=np.random.default_rng(17092026);pairs=0
for _ in range(1000):
    # Partial domain overlap and negative coordinates exercise discarded targets.
    donors=np.unique(np.r_[-2.,rng.uniform(-2,2,rng.integers(2,120)),2.])
    targets=np.unique(np.r_[-3.,rng.uniform(-3,3,rng.integers(2,120)),3.])
    sweep=MonotoneTargets(targets)
    for left,right in zip(donors[:-1],donors[1:]):
        expected=[(j,max(0.,min(right,b)-max(left,a))) for j,(a,b) in enumerate(zip(targets[:-1],targets[1:])) if min(right,b)>max(left,a)]
        actual=sweep(left,right)
        assert [x[0] for x in actual]==[x[0] for x in expected]
        assert np.array([x[1] for x in actual]).tobytes()==np.array([x[1] for x in expected]).tobytes()
    pairs+=1
report=json.loads((h/'fast-overlap-report.json').read_text());arrays=traces=0
for case in report['cases']:
    prefix=f"fast-overlap-{case['N']}-{case['kind']}"
    raws=[]
    for row in case['runs']:
        p=h/(prefix+'-'+row['label']+'.npz');t=h/(prefix+'-'+row['label']+'-records.json')
        assert sha256(p.read_bytes()).hexdigest()==row['raw_sha256']
        assert sha256(t.read_bytes()).hexdigest()==row['trace_sha256']
        raws.append((p,t))
    with np.load(raws[0][0]) as a,np.load(raws[1][0]) as b:
        assert a.files==b.files
        for key in a.files:assert a[key].dtype==b[key].dtype and a[key].shape==b[key].shape and a[key].tobytes()==b[key].tobytes();arrays+=1
    assert raws[0][1].read_bytes()==raws[1][1].read_bytes();traces+=1
out={'reviewer':'/root','author':'/root/s03_runtime_builder','verdict':'APPROVE_EXACT_SEARCH_OPTIMIZATION_ONLY','helper_sha256':sha256((h/'fast_overlap.py').read_bytes()).hexdigest(),'baseline_sha256':report['baseline_sha256'],'independent_random_partition_pairs':pairs,'paired_arrays':arrays,'paired_diagnostic_files':traces,'proof':'Sorted non-overlapping donors have nondecreasing left endpoints. A target with right<=left cannot overlap this or any later donor. Remaining target scan ends at first target left>=donor right. Original min/max expressions, ascending target order and all downstream donor/remainder arithmetic remain unchanged in the inspected hash-pinned generated method.','findings':[],'limits':['Private search preconditions come from validated ordered State partitions; no arbitrary unsorted donor support claimed.','Timings remain author measurements; no full solver speedup or numerical acceptance.','Integration must bind this exact helper and preserve state/diagnostic arithmetic.']}
(h/'parent-fast-review.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))

"""Software-only controlled RHS reproduces hidden inadmissible second FE."""
from pathlib import Path
from hashlib import sha256
import importlib.util,sys,json
import numpy as np
from run_controls import model

HERE=Path(__file__).resolve().parent
results=[]
for label,path in [('historical',HERE/'historical/before-second-fe-guard/prototype.py'),('fixed',HERE/'prototype.py')]:
    spec=importlib.util.spec_from_file_location('guard_'+label,path)
    m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)
    solver=m.RegionSolver(model())
    state=solver.initialize([0.,1.],[(600.,1e5,0.,(0.,0.,1.,0.,0.),(0.,0.,1.,0.))],('parcel',))
    calls=[0]
    def controlled_rhs(_):
        calls[0]+=1
        return np.array([0.,0. if calls[0]==1 else -1.5]),np.zeros((2,12))
    solver.rhs=controlled_rhs
    before=(state.edges.tobytes(),state.inventory.tobytes())
    try:
        final,_=solver.step(state,1.)
        result=dict(accepted=True,final_width=float(np.diff(final.edges)[0]))
    except m.TrialRejected as exc:
        result=dict(accepted=False,reason=str(exc))
    assert before==(state.edges.tobytes(),state.inventory.tobytes())
    results.append(dict(label=label,source_sha256=sha256(path.read_bytes()).hexdigest(),**result))
assert results[0]['accepted'] and not results[1]['accepted']
report=dict(classification='SOFTWARE_GUARD_REPRODUCER_NOT_PHYSICAL_CASE',
    controlled_FE1_width=1.,controlled_FE2_width=-.5,unprotected_combination_width=.25,
    input_byte_unchanged=True,results=results)
(HERE/'guard-reproducer.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))

from pathlib import Path
from hashlib import sha256
import types,sys,json,numpy as np
import area_solver as current
from run_controls import model
from dino2next.gasdynamics import PolynomialSegment
HERE=Path(__file__).resolve().parent
path=HERE/'historical/before-W-overlap/area_solver.py'
old=types.ModuleType('area02_old');old.__file__=str(HERE/'area_solver.py');sys.modules[old.__name__]=old
exec(compile(path.read_text(),str(path),'exec'),old.__dict__)
rows=[]
for name,module,source in [('historical',old,path),('corrected',current,HERE/'area_solver.py')]:
    edges=np.array([0.,.9,.9000000001,1.])
    solver=module.AreaHybrid(model(),edges,module.G.VolumeMap(PolynomialSegment(0.,1.,(1.,0.,2.),(1.,))))
    data=[(600.,1e5,0.,(0.,0.,1.,0.,0.),(0.,0.,1.,0.))]*3
    state=solver.initialize(edges,data,('L','M','R'));q,_,_=solver.sample(state,state.edges)
    rows.append(dict(version=name,source_sha256=sha256(source.read_bytes()).hexdigest(),
        thin_relative_mass_error=float((q[1,0]-state.inventory[1,0])/state.inventory[1,0]),
        self_projection_bitwise=q.tobytes()==state.inventory.tobytes()))
assert not rows[0]['self_projection_bitwise'] and rows[1]['self_projection_bitwise']
same={}
for filename in ('rest-control.npz','advisor-controls.npz'):
    a=np.load(HERE/filename);b=np.load(HERE/'historical/before-W-overlap'/filename)
    same[filename]=all(a[k].tobytes()==b[k].tobytes() for k in a.files)
assert all(same.values())
report=dict(classification='AREA02_REPRESENTATION_CORRECTION_NOT_NUMERICAL_ACCEPTANCE',
    reproducer=rows,prior_evolution_arrays_bitwise=same)
(HERE/'area02-reproducer.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))

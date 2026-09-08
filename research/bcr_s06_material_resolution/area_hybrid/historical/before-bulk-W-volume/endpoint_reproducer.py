"""Historical/corrected canonical endpoint initialization, no time evolution."""
from pathlib import Path
from hashlib import sha256
from fractions import Fraction
import types,sys,json
import numpy as np
import area_solver as current
from run_controls import model,physical
from dino2next.gasdynamics import PolynomialSegment

HERE=Path(__file__).resolve().parent
oldpath=HERE/'historical/before-endpoint-representation/area_solver.py'
old=types.ModuleType('historical_area_endpoint')
# Resolve unchanged dependency paths against their original source directory.
old.__file__=str(HERE/'area_solver.py');sys.modules[old.__name__]=old
exec(compile(oldpath.read_text(),str(oldpath),'exec'),old.__dict__)
rows=[]
for label,module,path in [('historical',old,oldpath),('fixed',current,HERE/'area_solver.py')]:
    grid=np.linspace(0,1,25)
    solver=module.AreaHybrid(model(),grid,module.G.VolumeMap(PolynomialSegment(0.,1.,(1.,0.,2.),(1.,))))
    try:
        state=solver.initialize(grid,physical(grid),('left',)*12+('right',)*12)
        row=dict(initialized=True,x_right=float(state.edges[-1]),W_right=float(state.W[-1]),endpoint_records=state.endpoint_records)
    except module.H.TrialRejected as exc:row=dict(initialized=False,reason=str(exc))
    rows.append(dict(label=label,source_sha256=sha256(path.read_bytes()).hexdigest(),**row))
assert not rows[0]['initialized'] and rows[1]['initialized']
report=dict(classification='CANONICAL_ENDPOINT_SOFTWARE_REPRODUCER_NOT_NUMERICAL_ACCEPTANCE',
    exact_volume='5/3',stored_volume=float(Fraction(5,3)),
    exact_residual=str(Fraction(5,3)-Fraction(float(Fraction(5,3)))),results=rows)
(HERE/'endpoint-reproducer.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))

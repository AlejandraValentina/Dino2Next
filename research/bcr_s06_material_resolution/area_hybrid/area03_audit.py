"""Bounded AREA03 software comparison; no numerical gate classification."""
import hashlib,json,types,sys
from pathlib import Path
import numpy as np
import area_solver as A
from run_controls import model
from dino2next.gasdynamics import PolynomialSegment
P=Path(__file__).resolve().parent
old=types.ModuleType('area03_historical');old.__file__=str(P/'area_solver.py')
sys.modules[old.__name__]=old
source=P/'historical/before-bulk-W-volume/area_solver.py'
exec(compile(source.read_text(),old.__file__,'exec'),old.__dict__)
rows=[]
for module in (old,A):
    x=np.array([.9,.9000000001,.9000000002])
    s=module.AreaHybrid(model(),x,A.G.VolumeMap(PolynomialSegment(0.,1.,(1.,0.,2.),(1.,))))
    state=s.initialize(x,[(600.,1e5,0.,(0.,0.,1.,0.,0.),(0.,0.,1.,0.))]*2,('L','L'))
    original=s.kernel.state;captured=[]
    def capture(mesh,Q):
        result=original(mesh,Q)
        captured.append(s.kernel.recover(Q/np.asarray(mesh.area_averages)[:,None]).V.copy())
        return result
    s.kernel.state=capture;s.rhs_options(state)
    direct=state.inventory/np.diff(state.W)[:,None]
    rows.append(dict(source='historical' if module is old else 'current',
        pressure=captured[0][:,2].tolist(),regional_pressure=s.recover(state)[:,2].tolist(),
        density_relative_error=(captured[0][:,0]/direct[:,0]-1).tolist(),
        unit_route_relative_error=((s.unit_state(state).inventory/np.diff(state.edges)[:,None])[:,0]/direct[:,0]-1).tolist()))
comparisons={}
for name in ('rest-control.npz','advisor-controls.npz'):
    before=np.load(P/'historical/before-bulk-W-volume'/name);after=np.load(P/name)
    comparisons[name]={k:dict(bitwise=before[k].tobytes()==after[k].tobytes(),max_abs=float(np.max(abs(before[k]-after[k])))) for k in before.files}
report=dict(classification='SOFTWARE_VOLUME_CONSISTENCY_NOT_VAL_ACCEPTANCE',probe=rows,controls=comparisons,
    hashes={str(p.relative_to(P)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [source,P/'area_solver.py',P/'advisor.py',Path(__file__)]})
(P/'area03-audit.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))

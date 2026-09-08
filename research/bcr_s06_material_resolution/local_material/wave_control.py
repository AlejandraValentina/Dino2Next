"""Physical-wave smoke control; no qualified reference or shock PASS claim."""
from pathlib import Path
import hashlib,json,time
import numpy as np
from prototype import LocalSolver
from run_controls import make_model

HERE=Path(__file__).resolve().parent
grid=np.linspace(-.5,1.5,25);solver=LocalSolver(make_model(),grid)
centers=(grid[:-1]+grid[1:])/2
physical=[(600.,200000. if x<1/6 else 100000.,0.,
           (0.,0.,1.,0.,0.) if x<.5 else (0.,0.,0.,1.,0.),
           (0.,0.,1.,0.)) for x in centers]
state=solver.initialize(grid,physical,tuple('L' if x<.5 else 'R' for x in centers))
initial=state;t=0.;steps=0;start=time.perf_counter();signed=np.zeros(12);throughput=np.zeros(12)
while t<.0008:
    state,flux,dt,failures=solver.advance(state,.0008-t)
    signed+=flux[0]-flux[-1];t+=dt;steps+=1
    rec=solver.stage_records[-1]
    for f in (np.array(rec['flux0']),np.array(rec['flux1'])):
        throughput+=.5*dt*(abs(f[0])+abs(f[-1]))
w=solver.recover(state);right=np.array([x=='R' for x in state.labels])
data={'classification':'PHYSICAL_WAVE_SMOKE_NOT_QUALIFIED_SHOCK_VERIFICATION',
      'elapsed_seconds':time.perf_counter()-start,'steps':steps,'time':t,
      'right_region_pressure_change_Pa':float(np.max(abs(w[right,2]-1e5))),
      'max_velocity':float(np.max(abs(w[:,1]))),'interface_position':float(state.edges[solver.interfaces(state)[0]]),
      'inventory_residual':(np.sum(state.inventory-initial.inventory,axis=0)-signed).tolist() if state.inventory.shape==initial.inventory.shape else (np.sum(state.inventory,axis=0)-np.sum(initial.inventory,axis=0)-signed).tolist(),
      'absolute_throughput':throughput.tolist(),
      'edges':state.edges.tolist(),'inventory':state.inventory.tolist(),'physical':w.tolist(),
      'stages':solver.stage_records,'remaps':solver.remap_records,'transactions':solver.transaction_records,'derived_records':solver.records,
      'source_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__),HERE/'prototype.py']}}
assert data['right_region_pressure_change_Pa']>1000
(HERE/'wave-result.json').write_text(json.dumps(data)+'\n')
print(json.dumps({k:data[k] for k in ('classification','elapsed_seconds','steps','right_region_pressure_change_Pa','max_velocity')}))

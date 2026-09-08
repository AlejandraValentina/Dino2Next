"""One directed thermal contact crossing, not a full validation campaign."""
from pathlib import Path
import hashlib,json,time
import numpy as np
from hybrid import HybridSolver
from run_controls import make_model

HERE=Path(__file__).resolve().parent
grid=np.linspace(-.5,1.5,25);s=HybridSolver(make_model(),grid)
x=.5+1e-10;edges=np.sort(np.r_[grid,x]);mid=(edges[:-1]+edges[1:])/2
rows=[(600. if v<x else 1800.,1e5,100.,(0.,0.,1.,0.,0.) if v<x else (0.,0.,0.,1.,0.),
       (1.,0.,0.,0.) if v<x else (0.,0.,1.,0.)) for v in mid]
state=s.initialize(edges,rows,tuple('L' if v<x else 'R' for v in mid));initial=state
rhoamb=s.model.evaluate(350.,1e5,(0.,.232,.768,0.,0.))
qref=rhoamb.rho*2*np.array([1.,rhoamb.a,rhoamb.cv*350.]+[1.]*9)
t=0.;signed=np.zeros(12);throughput=np.zeros(12);start=time.perf_counter();history=[];failures=[]
while t<.001:
    state,flux,dt,rejects=s.advance(state,.001-t);failures.extend(rejects)
    t+=dt;signed+=flux[0]-flux[-1]
    for f in (np.array(s.stage_records[-1]['flux0']),np.array(s.stage_records[-1]['flux1'])):
        throughput+=.5*dt*(abs(f[0])+abs(f[-1]))
    w=s.recover(state)
    history.append({'t':t,'edges':state.edges.tolist(),'inventory':state.inventory.tolist(),'labels':state.labels,
                    'max_pressure_error_Pa':float(np.max(abs(w[:,2]-1e5))),
                    'max_velocity_error':float(np.max(abs(w[:,1]-100.)))})
residual=np.sum(state.inventory,axis=0)-np.sum(initial.inventory,axis=0)-signed
scale=np.sum(abs(initial.inventory),axis=0)+throughput+qref;scale[3:]=scale[0]
assert np.max(abs(residual)/scale)<1e-10
report={'classification':'DIRECTED_HYBRID_FUNCTION_GUARD_DEMONSTRATION_NOT_VAL008_ACCEPTANCE',
        'elapsed_seconds':time.perf_counter()-start,'steps':len(history),'history':history,
        'max_pressure_error_Pa':max(r['max_pressure_error_Pa'] for r in history),
        'max_velocity_error':max(r['max_velocity_error'] for r in history),'failures':failures,
        'ST003_residual':residual.tolist(),'ST003_normalizer':scale.tolist(),'ST003_normalized':(abs(residual)/scale).tolist(),
        'ambient':{'T':350.,'p':1e5,'Y':[0.,.232,.768,0.,0.],'rho':rhoamb.rho,'cv':rhoamb.cv,'a':rhoamb.a},
        'absolute_throughput':throughput.tolist(),'qref':qref.tolist(),
        'stages':s.stage_records,'hybrid':s.hybrid_records,'guard_candidates':s.guard_records,'transactions':s.transaction_records,
        'initial_edges':initial.edges.tolist(),'initial_inventory':initial.inventory.tolist(),
        'source_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__),HERE/'hybrid.py',HERE/'prototype.py',HERE/'kernel_source.py',HERE.parent/'material/prototype.py']}}
(HERE/'hybrid-result.json').write_text(json.dumps(report)+'\n')
print(json.dumps({k:report[k] for k in ('classification','elapsed_seconds','steps','max_pressure_error_Pa','max_velocity_error','failures')}))

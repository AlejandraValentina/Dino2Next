"""Proposed volumetric step advisor; scientific extension, not a software fix."""
from pathlib import Path
from hashlib import sha256
import inspect,textwrap
import numpy as np
import area_solver as A

BASELINE_SHA256='3a98afd8d3a369d296b82f067f024f0b8035652298aed6c1498ce1a8cbbd424a'
assert sha256(Path(A.__file__).read_bytes()).hexdigest()==BASELINE_SHA256

def bounds(state,primitive,face_area,volume_speed):
    """Return each fixed-factor predictor and the local/global minimum.

    No positivity theorem is asserted for NASA. All physical stage guards remain.
    """
    V=np.diff(state.W);dx=np.diff(state.edges)
    area=np.asarray(face_area);Wdot=np.asarray(volume_speed)
    if np.any(V<=0) or np.any(dx<=0) or np.any(area<=0):raise A.H.TrialRejected('ADVISOR_GEOMETRY')
    speed=Wdot/area
    u,a=primitive[:,1],primitive[:,3]
    left=a+abs(u-speed[:-1]);right=a+abs(u-speed[1:])
    inherited=.2*(dx/np.maximum(left,right))
    volumetric=.2*(V/np.maximum(area[:-1]*left,area[1:]*right))
    Vdot=np.diff(Wdot);shrink=np.full(len(V),np.inf)
    negative=Vdot<0;shrink[negative]=.5*V[negative]/(-Vdot[negative])
    local=np.minimum(np.minimum(inherited,volumetric),shrink)
    if not np.all(np.isfinite(local)) or np.any(local<=0):raise A.H.TrialRejected('ADVISOR_NO_POSITIVE_DT')
    return dict(inherited_acoustic=inherited.tolist(),volumetric_acoustic=volumetric.tolist(),
                shrinking_volume=[None if np.isinf(x) else float(x) for x in shrink],
                volume=V.tolist(),volume_rate=Vdot.tolist(),face_area=area.tolist(),
                relative_left=left.tolist(),relative_right=right.tolist(),limit=float(np.min(local)))

class AdvisedAreaHybrid(A.AreaHybrid):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs);self.advisor_records=[]
    def evaluate_bounds(self,state):
        w=self.recover(state)
        Wdot,_,_,_,_,_=self.rhs_options(state)
        area=np.array([self.geometry.segment.value(float(x)) for x in state.edges])
        return bounds(state,w,area,Wdot)
    def suggested_dt(self,state,cfl=.2):
        if cfl!=.2:raise A.H.TrialRejected('ADVISOR_FIXED_ACOUSTIC_FACTOR')
        return self.evaluate_bounds(state)['limit']
    def check_dt(self,state,dt,stage):
        record=self.evaluate_bounds(state)
        record.update(transaction_id=self._transaction_id,stage=stage,requested_dt=dt,
                      admissible_dt=bool(np.isfinite(dt) and 0<dt<=record['limit']))
        self.advisor_records.append(record)
        if not record['admissible_dt']:raise A.H.TrialRejected('VOLUMETRIC_STAGE_BOUND_'+stage)

# Retain every flux, source, guard and stage operation; add endpoint predictors.
source=textwrap.dedent(inspect.getsource(A.AreaHybrid._step))
for old,new in (
    ("    self._context['stage']='Y0_RHS'","    self.check_dt(state,dt,'Y0')\n    self._context['stage']='Y0_RHS'"),
    ("    self._context['stage']='Y1_RHS'","    self.check_dt(stage,dt,'Y1')\n    self._context['stage']='Y1_RHS'")):
    assert source.count(old)==1
    source=source.replace(old,new)
namespace=dict(A.AreaHybrid._step.__globals__)
exec(compile(source,str(Path(__file__).with_name('advised_step.py')),'exec'),namespace)
AdvisedAreaHybrid._step=namespace['_step']
